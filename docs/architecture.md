# HostLens — Production Cloud Architecture

> **Document Type**: Architecture Reference  
> **Audience**: Engineering / Platform Teams  
> **Status**: Draft v1.0

---

## Overview

HostLens is designed as a modern, cloud-native data platform capable of scaling from a single-city proof-of-concept to a multi-region, multi-city deployment processing millions of Airbnb-equivalent listing events per day. This document describes the production architecture, cost estimates per layer, and trade-off analysis for key design decisions.

---

## End-to-End Architecture Diagram

```mermaid
flowchart TD
    subgraph INGESTION["🛬 Layer 1 — Ingestion"]
        A1["Inside Airbnb\n(Public API/CSV Dumps)"]
        A2["Streaming Events\n(Simulated via Kafka/Kinesis)"]
        A3["External APIs\n(Weather, Events, Transit)"]
    end

    subgraph LANDING["🪣 Layer 2 — Raw Landing (Cloud Storage)"]
        B1["AWS S3 / GCS Bucket\n(listings/, calendar/, reviews/)"]
        B2["Event Stream\n(Kafka Topic: price_updates)"]
    end

    subgraph PROCESSING["⚙️ Layer 3 — Processing & Transformation"]
        C1["AWS Glue / Dataflow\n(Batch ETL — Schema Validation)"]
        C2["Apache Spark\n(Large-Scale Deduplication & Enrichment)"]
        C3["Flink / Kinesis Analytics\n(Stream Processing — Price Alerts)"]
        C4["dbt (Data Build Tool)\n(Staging → Marts Transformations)"]
    end

    subgraph STORAGE["🗄️ Layer 4 — Analytical Storage"]
        D1["Snowflake / BigQuery\n(Data Warehouse — Star Schema)"]
        D2["DuckDB\n(Local Analytics / Dev)"]
        D3["Redis Cache\n(Low-latency API responses)"]
    end

    subgraph ML["🤖 Layer 5 — ML Platform"]
        E1["MLflow / Vertex AI\n(Model Registry & Tracking)"]
        E2["Scikit-Learn / XGBoost\n(Batch Pricing Models)"]
        E3["LLM Gateway\n(RAG Q&A via Vertex AI / OpenAI)"]
        E4["Feature Store\n(Feast — precomputed features)"]
    end

    subgraph SERVING["🚀 Layer 6 — Serving & Visualization"]
        F1["FastAPI / Flask\n(REST API for pricing predictions)"]
        F2["Streamlit Dashboard\n(Internal Analytics UI)"]
        F3["Looker / Metabase\n(BI for stakeholders)"]
        F4["Alerts & Notifications\n(PagerDuty / Slack Webhooks)"]
    end

    subgraph GOVERNANCE["🛡️ Layer 7 — Governance & Observability"]
        G1["Great Expectations\n(Data Quality Gates)"]
        G2["OpenLineage / Marquez\n(Data Lineage Tracking)"]
        G3["Prometheus + Grafana\n(Infrastructure Monitoring)"]
        G4["Responsible AI Framework\n(SHAP, PSI Drift Detection)"]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B1
    B1 --> C1
    B2 --> C3
    C1 --> C2
    C2 --> C4
    C3 --> D3
    C4 --> D1
    D2 -.->|Dev/Local Mode| C4
    D1 --> E4
    D1 --> F2
    D1 --> F3
    E4 --> E2
    E2 --> E1
    E1 --> F1
    E3 --> F2
    F1 --> F4
    D1 --> G1
    C4 --> G2
    F1 --> G3
    E2 --> G4
```

---

## Layer-by-Layer Cost Estimates

*Estimates assume processing 5 million listing records per month, 1TB data warehouse, 2 ML training jobs/day.*

| Layer | Service | Configuration | Est. Monthly Cost (USD) |
|:---|:---|:---|---:|
| **Ingestion** | AWS Glue Crawlers | 10 DPU-hours/day | $43 |
| **Landing Storage** | AWS S3 Standard | 500 GB raw data | $11 |
| **Stream Processing** | AWS Kinesis Analytics | 2 KPUs, 8h/day | $128 |
| **Batch ETL** | AWS Glue ETL Jobs | 20 DPU-hours/day | $87 |
| **Data Warehouse** | Snowflake (On-Demand) | 2 X-Small warehouses | $230 |
| **ML Training** | AWS SageMaker | ml.m5.large, 2h/day | $90 |
| **Feature Store** | Feast on Redis | r6g.large Redis | $105 |
| **LLM (RAG)** | OpenAI API (GPT-4o) | 2M tokens/month | $20 |
| **Serving API** | AWS ECS Fargate | 0.5 vCPU, 1GB RAM × 2 | $35 |
| **Dashboard** | Streamlit Cloud / ECS | 2 vCPU, 4GB RAM | $60 |
| **Monitoring** | Grafana Cloud Free Tier | 10k metrics/month | $0 |
| **Data Quality** | Great Expectations OSS | Self-hosted | $0 |
| **Total** | | | **~$809/month** |

> **Note**: At multi-city scale (50 cities), costs scale approximately linearly for storage/processing but sub-linearly for ML serving (shared model). Estimated total at 50 cities: **~$3,200/month** with BigQuery replacing Snowflake for cost savings.

---

## Alternative Architecture Comparison

| Architecture | Latency | Scalability | Cost/Month | Complexity | Best For |
|:---|:---:|:---:|---:|:---:|:---|
| **DuckDB + Local (Current)** | <1s | Single node | $0 | Low | Dev/POC |
| **BigQuery + Dataflow** | 2–5s | Global | ~$400 | Medium | Growing teams |
| **Snowflake + Spark** | 3–8s | Enterprise | ~$800 | High | Large enterprises |
| **Databricks Lakehouse** | 1–3s | Global | ~$1,200 | High | Data science teams |
| **AWS Native (Redshift+Glue)** | 2–6s | Regional | ~$650 | Medium | AWS-committed orgs |

---

## Key Design Decisions & Trade-offs

### Decision 1: DuckDB vs. BigQuery for Analytics
| Factor | DuckDB | BigQuery |
|:---|:---|:---|
| **Setup Time** | Minutes | Hours (IAM, billing) |
| **Cost at Small Scale** | $0 | $5/TB queried |
| **Concurrent Users** | Limited (1 writer) | Thousands |
| **Verdict** | ✅ Chosen for POC | → Migrate at >10 concurrent users |

### Decision 2: Batch vs. Stream Processing
| Factor | Batch (Current) | Stream (Planned) |
|:---|:---|:---|
| **Data Freshness** | Hours | Seconds |
| **Infrastructure Cost** | Low | 3–4× higher |
| **Complexity** | Low | High |
| **Use Case** | Historical analytics | Real-time alerts |
| **Verdict** | ✅ Chosen for analytics | Stream for price monitoring only |

### Decision 3: Self-hosted ML vs. Managed (Vertex AI/SageMaker)
| Factor | Self-hosted (Scikit-Learn) | Managed (Vertex AI) |
|:---|:---|:---|
| **Model Portability** | High | Vendor lock-in risk |
| **MLOps Features** | Manual | Built-in |
| **Cost** | Compute only | 30–40% premium |
| **Verdict** | ✅ Chosen for POC | → Migrate at >20 models |

---

## Scalability Roadmap

```
Phase 1 (Current) → Phase 2 (6 months) → Phase 3 (18 months)
DuckDB + Local         BigQuery + Airflow     Snowflake + Spark + Kafka
Single-city           5 cities              50+ cities
$0/month              ~$400/month           ~$3,200/month
```
