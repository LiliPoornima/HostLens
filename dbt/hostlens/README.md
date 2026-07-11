# HostLens — dbt Project

This directory contains the **dbt (Data Build Tool)** project for HostLens.
It transforms the raw DuckDB tables produced by the ETL pipeline into clean,
documented, and tested analytical models consumed by the dashboard and BI tools.

---

## Project Structure

```
dbt/hostlens/
├── dbt_project.yml          # Project configuration
├── profiles.yml             # DuckDB connection profile
├── models/
│   ├── schema.yml           # All model + column documentation + dbt tests
│   ├── staging/
│   │   ├── stg_listings.sql   # Staged listings (view)
│   │   ├── stg_hosts.sql      # Staged host profiles (view)
│   │   └── stg_reviews.sql    # Staged reviews (view)
│   └── marts/
│       ├── mart_borough_pricing.sql    # Borough × room type pricing (table)
│       └── mart_host_performance.sql  # Host KPIs + performance score (table)
└── README.md
```

---

## Prerequisites

1. **Python venv active** with HostLens dependencies installed.
2. **ETL pipeline run first** so that DuckDB tables exist:
   ```powershell
   .\\venv\\Scripts\\python.exe src/pipeline.py
   ```
3. **dbt-duckdb installed**:
   ```powershell
   .\\venv\\Scripts\\pip install dbt-duckdb
   ```

---

## Running dbt Models

All commands must be run from the `dbt/hostlens/` directory.

### 1. Verify Connection
```bash
dbt debug --profiles-dir .
```

### 2. Run All Models (staging → marts)
```bash
dbt run --profiles-dir .
```

### 3. Run Only Staging Models
```bash
dbt run --profiles-dir . --select staging
```

### 4. Run Only Mart Models
```bash
dbt run --profiles-dir . --select marts
```

### 5. Run dbt Tests
Executes all `not_null`, `unique`, `accepted_values`, and `relationships` tests
defined in `models/schema.yml`:
```bash
dbt test --profiles-dir .
```

### 6. Generate Documentation Site
```bash
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
# Opens at http://localhost:8080 — includes lineage graph
```

---

## Data Lineage

```
fact_listings (source) ──► stg_listings ──► mart_borough_pricing
                                         └──► mart_host_performance
dim_hosts (source)     ──► stg_hosts    ──►  mart_host_performance
dim_reviews (source)   ──► stg_reviews
```

---

## Model Descriptions

| Model | Type | Description |
|:---|:---|:---|
| `stg_listings` | View | Cleaned listing records with type casts and quality filters |
| `stg_hosts` | View | Host profiles with boolean normalization and tenure calculation |
| `stg_reviews` | View | Reviews with parsed dates and comment length metrics |
| `mart_borough_pricing` | Table | Borough × room type pricing KPIs for BI and dashboard |
| `mart_host_performance` | Table | Host-level KPIs with composite performance score (0–100) |

---

## dbt Tests Summary

| Test | Column | Model |
|:---|:---|:---|
| `not_null` | listing_id | stg_listings |
| `unique` | listing_id | stg_listings |
| `accepted_values` | borough | stg_listings |
| `accepted_values` | room_type | stg_listings |
| `not_null` + `unique` | host_id | stg_hosts |
| `not_null` + `unique` | review_id | stg_reviews |
| `relationships` | listing_id → stg_listings | stg_reviews |
| `not_null` | borough, room_type | mart_borough_pricing |
| `not_null` + `unique` | host_id | mart_host_performance |
