# HostLens — Cost Optimization Design

> **Document Type**: Engineering Cost Analysis  
> **Audience**: Platform Engineering, Product Leadership  
> **Scope**: Global-scale deployment (50+ cities, 100M+ listing events/year)

---

## Executive Summary

At the current single-city NYC scale, HostLens runs at zero infrastructure cost on DuckDB.  
This document provides a rigorous cost optimization strategy for scaling globally, with actionable recommendations that can reduce projected infrastructure costs by **40–55%** compared to a naive cloud-first approach.

---

## Global Scale Cost Projections

Assumptions for global scale:
- **50 cities** with full Airbnb dataset ingestion
- **100M listing records/year** ingested
- **5TB** analytical data warehouse
- **500 daily active users** on the dashboard
- **10 ML training jobs/day** across cities

| Component | Naive (Unoptimized) | Optimized | Monthly Saving |
|:---|---:|---:|---:|
| Data Warehouse (Snowflake) | $2,400 | $960 (BigQuery flat-rate) | $1,440 |
| ETL Processing (Spark on EMR) | $1,800 | $720 (Spot Instances 60%) | $1,080 |
| ML Training (On-Demand GPU) | $900 | $360 (Spot + Preemptible) | $540 |
| Storage (S3 Standard) | $230 | $80 (S3 Intelligent-Tiering) | $150 |
| Dashboard Serving (ECS) | $480 | $190 (Fargate Spot) | $290 |
| LLM/RAG API Calls | $800 | $180 (Caching + smaller model) | $620 |
| Monitoring & Alerting | $200 | $0 (OSS: Prometheus/Grafana) | $200 |
| **Total** | **$6,810/month** | **$2,490/month** | **$4,320 (63% saving)** |

---

## Optimization Strategy 1 — Compute Cost Reduction

### Spot / Preemptible Instances
ML training workloads are **fault-tolerant and restartable**. Migrating from on-demand to AWS Spot or GCP Preemptible instances reduces compute costs by 60–80%.

```
On-demand ml.m5.xlarge:  $0.23/hour
Spot ml.m5.xlarge:        $0.07/hour  (70% saving)
```

**Implementation**: Use AWS SageMaker Managed Spot Training with `MaxWaitTimeInSeconds` checkpointing.

### Batch Window Scheduling
Trigger ETL jobs during **off-peak hours (02:00–06:00 UTC)** when cloud spot availability is highest and prices are lowest.

---

## Optimization Strategy 2 — Storage Tiering

| Data Category | Access Frequency | Recommended Tier | Cost/GB/Month |
|:---|:---|:---|---:|
| Recent listings (last 30 days) | Daily | S3 Standard | $0.023 |
| Historical listings (31–365 days) | Weekly | S3 Standard-IA | $0.0125 |
| Archive (>1 year) | Monthly | S3 Glacier | $0.004 |
| Analytical warehouse (hot) | Real-time | BigQuery active | $0.02 |
| Analytical warehouse (cold) | Monthly | BigQuery long-term | $0.01 |

**Projected Saving**: Applying Intelligent-Tiering on 5TB reduces storage costs from $230 to $80/month.

---

## Optimization Strategy 3 — LLM / RAG Cost Reduction

The RAG Q&A console is the highest per-query cost component. Three optimizations:

### 3a. Semantic Caching
Cache LLM responses for semantically similar questions using a vector similarity threshold (cosine > 0.92). Estimated **cache hit rate: 70%** for repeat analytical queries.

```python
# Pseudocode for semantic caching
cache = RedisVectorStore()
if cache.similarity_search(query, threshold=0.92):
    return cache.get(query)
else:
    response = llm.generate(query)
    cache.store(query, response)
    return response
```

### 3b. Model Routing (LLM Cascade)
Route queries by complexity:
- **Simple factual queries** → smaller model (GPT-4o-mini, $0.15/1M tokens)
- **Complex synthesis queries** → full model (GPT-4o, $5.00/1M tokens)

**Estimated saving**: 75% of queries are routable to the smaller model → **70% cost reduction**.

### 3c. Retrieval Optimization
Limit retrieved context to top-5 most relevant review chunks instead of top-20. Reduces token usage per query by 60% with minimal quality loss.

---

## Optimization Strategy 4 — Data Warehouse Query Optimization

### Partitioning
Partition the fact_listings table by `borough` and `snapshot_date`. Queries filtered by borough (the most common filter pattern) scan **~20% of the data** instead of 100%.

```sql
-- BigQuery partitioned table definition
CREATE TABLE hostlens.fact_listings
PARTITION BY DATE(snapshot_date)
CLUSTER BY borough, room_type AS
SELECT * FROM staging.stg_listings;
```

**Estimated saving**: 5TB warehouse scanned → 1TB effective scan per query → **80% BigQuery query cost reduction**.

### Materialized Views
Pre-compute the 10 most expensive analytical queries (borough aggregations, host KPIs, price distributions) as materialized views refreshed every 6 hours.

---

## Optimization Strategy 5 — Multi-Tenancy & Shared Infrastructure

At 50 cities, **share ML serving infrastructure** across cities:
- One pricing model per region (not per city)
- Fine-tuned with city-specific residuals via lightweight adapter layers
- Single feature store shared across all cities

**Infrastructure reuse factor**: 50 cities share 6 model endpoints instead of 50 → **88% serving cost reduction**.

---

## Break-Even Analysis

| Transition Point | When to Migrate |
|:---|:---|
| DuckDB → BigQuery | >10 concurrent dashboard users OR >100GB warehouse |
| Batch only → Add Streaming | When data freshness SLA < 1 hour required |
| Self-hosted ML → Vertex AI | >20 models in production OR >5 engineers on ML team |
| Single-region → Multi-region | >10 cities OR latency SLA <200ms globally required |

---

## Summary Recommendations

1. **Immediately**: Apply S3 Intelligent-Tiering to all raw data (~$150/month saving from day one)
2. **3 months**: Switch ML training to Spot Instances (~$540/month saving)
3. **6 months**: Implement semantic caching for LLM queries (~$620/month saving)
4. **12 months**: Migrate to BigQuery with table partitioning on a flat-rate commitment (~$1,440/month saving)
5. **18 months**: Consolidate to regional ML serving with shared feature store (~$1,500/month saving at scale)

**Total optimized TCO at 50-city scale: ~$2,490/month vs. $6,810 unoptimized (63% reduction)**
