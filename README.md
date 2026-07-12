# HostLens: Airbnb Data Engineering & Analytics Project

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hostlens.streamlit.app/)

HostLens is an end-to-end data engineering and analytics project built on the public Inside Airbnb dataset. It covers ingestion, cleaning, enrichment, clustering, statistical analysis, forecasting, machine learning, and dashboarding across **New York City**, **Boston**, and **San Francisco**. The project is structured as a reproducible pipeline with supporting dbt models, tests, and reporting artifacts.

---

## Assignment Summary

### Completed Work
I completed the core pipeline and analysis workflow required for a realistic Airbnb market study. The submission includes data ingestion, preprocessing, feature engineering, clustering, statistical testing, pricing model development, occupancy forecasting, dashboard presentation, and validation artifacts. The work is organized so it can be reviewed stage by stage rather than as a single monolithic script.

### Incomplete Work
I did not fully implement a live production deployment or a real-time streaming system. Some cloud-scale and MLOps elements are documented as target architecture or simulated components rather than fully deployed infrastructure. That scope was intentionally deferred so the submission could prioritize the most important assessment goal: a working, reproducible end-to-end data pipeline with clear analytical outputs.

### 🌐 Live Deployment
The platform is deployed and publicly accessible at:  
👉 **[https://hostlens.streamlit.app/](https://hostlens.streamlit.app/)**

---

## Deliverables & Recommended Review Order

To review the project deliverables systematically, please follow this sequence:

1. **`README.md`** (This file): Establishes system context, setup instructions, and component outlines.
2. **Deployed Dashboard [https://hostlens.streamlit.app/](https://hostlens.streamlit.app/)**:
   * Interactive market overview, map exploration, model explainability, and occupancy forecasting.
   * Includes a simulated streaming experience for demonstrating event-driven monitoring concepts.
   * Switch between **NYC**, **Boston**, and **San Francisco** dynamically in the sidebar.
3. **`reports/HostLens_Executive_Report.pdf`**: A comprehensive analytical report compiling statistical inferences (H1-H5 with Bonferroni correction), ML pricing modeling performance, occupancy forecasting, and cost governance.
4. **dbt Transformation Layer ([dbt/hostlens/](file:///c:/Users/Poornima%20Liyanage/Documents/GitHub/HostLens/dbt/hostlens/))**: Validates staging views, mart models, documentation, and the 24 database constraints.
5. **Automated Test Suite ([tests/](file:///c:/Users/Poornima%20Liyanage/Documents/GitHub/HostLens/tests/))**: Includes 40+ unit and data quality tests certifying pipeline schemas, boundary ceilings, and null thresholds.
6. **Cloud Production Abstractions ([docs/](file:///c:/Users/Poornima%20Liyanage/Documents/GitHub/HostLens/docs/))**: Reviews the production 7-layer cloud design schema and the 63.4% budget optimization waterfall calculations.

---

## Security, Privacy & Anonymization
* **No hardcoded credentials**: The repository does not contain API keys, database passwords, or cloud access tokens. Simulated configuration is used where needed.
* **PII scrubbing**: Guest names, reviewer identifiers, and exact geographic coordinates are masked or removed during ETL ingestion. Spatial analysis is performed on grouped or aggregated location fields.

---

## Quick Start & Reproducibility

### Prerequisites
- **Python 3.11+**
- **pip** (Python package installer)

### Environment Setup
Clone the repository and run the setup commands to build the virtual environment and install dependencies:
```powershell
# Set execution policy if blocked on Windows PowerShell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Build virtual environment & install requirements
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

### Run the Ingestion & ETL Pipeline
Run the master ingestion, data profiling, cleaning, enrichment, database loading, and clustering pipeline for any city (`nyc`, `boston`, or `sf`):
```powershell
# Run NYC Ingest
.\venv\Scripts\python.exe src/pipeline.py --city nyc

# Run Boston Ingest
.\venv\Scripts\python.exe src/pipeline.py --city boston

# Run San Francisco Ingest
.\venv\Scripts\python.exe src/pipeline.py --city sf
```

### Run the Machine Learning & Statistics Pipeline
Train pricing prediction/explainability models, compile forecasts, and run statistical hypothesis tests for each market:
```powershell
# NYC Analytics
.\venv\Scripts\python.exe src/machine_learning.py --city nyc
.\venv\Scripts\python.exe src/forecasting.py --city nyc
.\venv\Scripts\python.exe src/statistics_analysis.py --city nyc

# Boston Analytics
.\venv\Scripts\python.exe src/machine_learning.py --city boston
.\venv\Scripts\python.exe src/forecasting.py --city boston
.\venv\Scripts\python.exe src/statistics_analysis.py --city boston

# San Francisco Analytics
.\venv\Scripts\python.exe src/machine_learning.py --city sf
.\venv\Scripts\python.exe src/forecasting.py --city sf
.\venv\Scripts\python.exe src/statistics_analysis.py --city sf
```

### Compile and Run the dbt Project
Verify database transformations, materialize analytical marts, and run data quality checks using dbt:
```powershell
cd dbt/hostlens
..\..\venv\Scripts\dbt run --profiles-dir .
..\..\venv\Scripts\dbt test --profiles-dir .
```

### Execute the Automated Test Suite
Run the full suite of unit and data quality validation tests with pytest:
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### Run the Streamlit Dashboard Locally
Launch the interactive web interface to view analytics, run stream simulations, and inspect architecture locally:
```powershell
.\venv\Scripts\python.exe -m streamlit run src/dashboard.py
```

### Compile the PDF Executive Report
Regenerate the comprehensive analytical PDF report:
```powershell
.\venv\Scripts\python.exe src/generate_pdf_report.py
```

---

## Project Structure

```
HostLens/
├── data/
│   ├── raw/                 # Raw Inside Airbnb CSV files (ignored in Git)
│   └── processed/           # Cleaned CSVs and hostlens_*.db (committed DuckDB files)
├── dbt/hostlens/            # dbt analytical project
│   ├── models/              # Staging views & business mart tables
│   ├── dbt_project.yml      # dbt project configurations
│   └── profiles.yml         # DuckDB connection profile
├── docs/                    # Architectural and strategy documents
│   ├── architecture.md      # Detailed cloud deployment diagram
│   └── cost_optimization.md # Cost reduction strategy at global scale
├── reports/                 # Pipeline logs, JSON/CSV reports (permutation importance, forecasts, etc.)
├── src/                     # Core Python engine
│   ├── pipeline.py          # Master ETL orchestrator (downloads, cleans, clusters, loads database)
│   ├── statistics_analysis.py # Statistical testing (H1-H5) & driver OLS
│   ├── machine_learning.py  # Pricing prediction models & feature importance
│   ├── forecasting.py       # Time-series occupancy forecasts
│   ├── stream_processor.py  # Kafka-style streaming alert engine simulation
│   └── dashboard.py         # Streamlit UI application
├── tests/                   # Pytest automation suite
│   ├── conftest.py          # Pytest setup & directory routing configuration
│   ├── test_pipeline.py     # ETL schema, ceilings, and null thresholds
│   ├── test_data_quality.py # Artifact validation (forecasts, clusters)
│   └── test_ml.py           # Prediction verification and model loading
├── requirements.txt         # Project package dependencies
└── README.md                # System documentation (This file)
```

---

## Streamlit Dashboard Tabs

The platform features a **12-tab dashboard** styled with custom CSS:

1. **📊 Market Overview**: High-level market KPIs, price distributions, and revenue insights.
2. **🗺️ Map Explorer**: Interactive scatter maps of listings colored by price, centered dynamically for the selected city.
3. **👥 Host & Reviews**: Detailed review word-clouds and host verification/status profiles.
4. **🤖 ML & Explainability**: Model comparisons (Random Forest, XGBoost, Linear) and interactive SHAP value explainers.
5. **🔮 Occupancy Forecast**: Multi-month time-series occupancy forecasting charts.
6. **⚙️ Pipeline Telemetry**: Logs and execution metrics of the DuckDB ETL run.
7. **💻 SQL Console**: SQL query shell directly querying the active city's DuckDB database.
8. **🤖 AI Intelligence Hub**: RAG-based Guest Reviews Q&A Console, Content-based Listing Recommender, and AI Listing Description Generator.
9. **📐 Statistical Analysis**: Bonferroni-corrected hypothesis test evaluations.
10. **⚙️ MLOps & Governance**: Model registry telemetry, drift thresholds, and model bias analysis.
11. **☁️ Architecture & Streaming**: End-to-end cloud infrastructure layouts, cost waterfalls, and a simulated streaming view for event-driven monitoring examples.
12. **🌍 Cross-City Comparison**: Multi-market comparison comparing metrics (price, ratings, superhosts) across NYC, Boston, and SF.

---

## 7-Layer Production Cloud Architecture

To illustrate how the project could scale beyond a local prototype, the documentation outlines a 7-layer cloud-native architecture:

1. **Ingestion**: Inside Airbnb API & streaming updates pulled via AWS ECS Fargate tasks.
2. **Landing**: RAW listing data landed on AWS S3 / Google Cloud Storage, with live updates routed through Apache Kafka topics.
3. **Processing**: Serverless ETL jobs managed by AWS Glue (PySpark) or Google Cloud Dataflow (Apache Beam) to clean and structure incoming logs.
4. **Storage**: Centralized enterprise data warehouse using Snowflake or Google BigQuery, partitioned by borough and transaction date.
5. **ML Platform**: Scikit-Learn, XGBoost, and lightweight adapters logged via MLflow Model Registry, serving inference via FastAPI endpoints.
6. **Serving**: BI layer serving dashboard users via Streamlit, Looker, or Power BI.
7. **Governance**: Data quality checks enforced via Great Expectations, lineage monitored by OpenLineage, and infrastructure health reported in Prometheus / Grafana.

---

## Global-Scale Cost Optimization Design

A naive 50-city deployment costs **$6,810/month**. Using our five targeted optimization strategies, we reduce monthly costs by **63.4%** to **$2,490/month**:

- **AWS Spot Instances**: Offload batch ML model training workloads. **Saves $540/mo**.
- **LLM Caching & Mini Cascading**: Route 75% of simple AI queries to GPT-4o-mini and utilize a semantic database cache. **Saves $620/mo**.
- **S3 Intelligent-Tiering**: Move historical listing snapshots to low-cost archival layers. **Saves $150/mo**.
- **BigQuery flat-rate/Snowflake Auto-Suspend**: Use pre-purchased capacity reservations and suspend inactive nodes. **Saves $1,440/mo**.
- **Shared Model Serving**: Serve per-city ML models through lightweight regional adapters rather than dedicated isolated endpoints. **Saves $1,570/mo**.

---

## AI & Assistive Tools Disclosure

Consistent with professional guidelines, we explicitly disclose the use of artificial intelligence and automated engineering tools in the development of this platform:

1. **Code Generation & Refactoring**: AI-assisted tools were used to scaffold project components, compile ReportLab PDF tables, build unit tests, format Streamlit custom CSS, and draft dbt SQL views.
2. **Data Enrichment**: Built-in mock LLM gateways and prompt templates in `src/ai_agent.py` simulate production RAG pipelines for review summarization.
3. **Validation**: Automated testing scripts verify and ensure that no hallucinated or syntactically invalid code is committed. All credentials, API keys, and personal identifier data have been excluded.
