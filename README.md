# HostLens: Advanced Airbnb Data Engineering & Analytics Platform

HostLens is an end-to-end, enterprise-grade data engineering, machine learning, and analytical platform built on top of the **Inside Airbnb NYC dataset**. It scales from a single-city DuckDB proof-of-concept into a highly optimized, 7-layer production cloud architecture designed to ingest, process, clean, model, and serve listing analytics.

---

## 🔍 Recommended Artifact Review Order

For the most cohesive walkthrough of this project, we recommend reviewing deliverables in the following sequence:

1. **`README.md`** (This file): Establishes system context, build requirements, and component outlines.
2. **`reports/HostLens_Executive_Report.pdf`**: The primary compilation summarizing the entire analysis (statistical inference, ML performance, forecasting, and governance).
3. **Interactive Streamlit Dashboard (`src/dashboard.py`)**: Runs the full UI including ML explanation models, MLOps retraining tabs, and real-time Kafka simulation feeds.
4. **Cloud Production Abstractions (`docs/` & Tab 11)**: Evaluates the production 7-layer design schema and the 63.4% budget optimization waterfall calculations.
5. **dbt Transformation project (`dbt/hostlens/`)**: Validates staging views, mart models, documentation, and the 24 dbt test constraints.
6. **Automated Pytest Suite (`tests/`)**: Reviews automation test cases certifying pipeline compliance and data thresholds.

---

## 🔒 Security & Privacy Compliance
* **API Keys & Credentials**: No hardcoded API keys, database access tokens, or cloud platform passwords exist within this repository. Config parameters are loaded locally or simulated.
* **PII & Privacy**: Guest names, reviewer identifiers, and exact geographic addresses have been scrubbed or masked during ETL ingestion. Spatial parameters are aggregated to listing cluster IDs.

---


## 🚀 Quick Start & Reproducibility

### 1. Prerequisites
- **Python 3.11+**
- **pip** (Python package installer)

### 2. Environment Setup
Clone the repository and run the setup script to initialize the virtual environment and install all dependencies:
```powershell
# Set execution policy if blocked on Windows PowerShell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Build virtual environment & install requirements
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

### 3. Run the End-to-End Pipeline
To run the full ingestion, data profiling, cleaning, enrichment, database DDL loading, and clustering pipeline:
```powershell
.\venv\Scripts\python.exe src/pipeline.py
```

### 4. Run Machine Learning & Statistics Pipeline
Train the pricing prediction and explainability models, calculate forecasts, and run stats inference tests:
```powershell
.\venv\Scripts\python.exe src/machine_learning.py
.\venv\Scripts\python.exe src/forecasting.py
.\venv\Scripts\python.exe src/statistics_analysis.py
```

### 5. Compile & Run the dbt Project
Verify database transformations, materialize analytics marts, and run data quality checks using dbt:
```powershell
cd dbt/hostlens
..\..\venv\Scripts\dbt run --profiles-dir .
..\..\venv\Scripts\dbt test --profiles-dir .
```

### 6. Execute the Automated Test Suite
Run the suite of 40+ unit and data quality tests with pytest:
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### 7. Launch the Streamlit Dashboard
Launch the interactive browser interface to view analytics, run stream simulations, and inspect architecture:
```powershell
.\venv\Scripts\python.exe -m streamlit run src/dashboard.py
```

### 8. Compile the PDF Executive Report
Regenerate the comprehensive 24-page analytical PDF report:
```powershell
.\venv\Scripts\python.exe src/generate_pdf_report.py
```

---

## 📂 Project Structure

```
HostLens/
├── data/
│   ├── raw/                 # Raw Inside Airbnb CSV files
│   └── processed/           # Cleaned CSVs and hostlens.db (DuckDB)
├── dbt/hostlens/            # dbt analytical project
│   ├── models/              # Staging views & business mart tables
│   ├── dbt_project.yml      # dbt project configurations
│   └── profiles.yml         # Local DuckDB connection profile
├── docs/                    # Architectural and strategy documents
│   ├── architecture.md      # Detailed cloud deployment diagram
│   └── cost_optimization.md # Cost reduction strategy at global scale
├── reports/                 # Pipeline logs, JSON and CSV metrics outputs
├── src/                     # Core Python engine
│   ├── pipeline.py          # Master ETL orchestrator
│   ├── statistics_analysis.py # Statistical testing (H1-H5) & driver OLS
│   ├── machine_learning.py  # Pricing prediction models & SHAP
│   ├── forecasting.py       # Prophetic time-series occupancy forecasts
│   ├── stream_processor.py  # Kafka-style streaming alert engine simulation
│   └── dashboard.py         # Premium Streamlit UI application
├── tests/                   # Pytest automation suite
│   ├── conftest.py          # Pytest setup & directory routing configuration
│   ├── test_pipeline.py     # ETL schema, ceilings, and null thresholds
│   ├── test_data_quality.py # Artifact validation (forecasts, clusters)
│   └── test_ml.py           # Prediction verification and model loading
├── requirements.txt         # Project package dependencies
└── README.md                # System documentation (This file)
```

---

## 🖥️ Streamlit Interactive Dashboard Tabs

The platform features a **11-tab premium dashboard** styled with custom CSS:

1. **📊 Market Overview**: High-level market KPIs, price distributions, and revenue insights.
2. **🗺️ Map Explorer**: Interactive scatter maps of listings colored by price and borough.
3. **👥 Host & Reviews**: Detailed review word-clouds and host verification/status profiles.
4. **🤖 ML & Explainability**: Model comparisons (Random Forest, XGBoost, Linear) and interactive SHAP value explainers.
5. **🔮 Occupancy Forecast**: Multi-month time-series occupancy forecasting charts.
6. **⚙️ Pipeline Telemetry**: Logs and execution metrics of the DuckDB ETL run.
7. **💻 SQL Console**: SQL query shell directly querying the local DuckDB database.
8. **🤖 AI Intelligence Hub**: LLM listing reviews summarization interface.
9. **📐 Statistical Analysis**: Bonferroni-corrected hypothesis test evaluations.
10. **⚙️ MLOps & Governance**: Model registry telemetry, drift thresholds, and model bias analysis.
11. **☁️ Architecture & Streaming**: End-to-end cloud infrastructure layouts, cost waterfalls, and a **Live Kafka Streaming Simulation** where you can trigger random price events and catch real-time neighborhood anomalies.

---

## 🏗️ 7-Layer Production Cloud Architecture

To scale HostLens to 50+ cities (100M+ events/year), the system transitions from a single-node DuckDB database to a fully-managed cloud-native lakehouse:

1. **Ingestion**: Inside Airbnb API & streaming updates pulled via AWS ECS Fargate tasks.
2. **Landing**: RAW listing data landed on AWS S3 / Google Cloud Storage, with live updates routed through Apache Kafka topics.
3. **Processing**: Serverless ETL jobs managed by AWS Glue (PySpark) or Google Cloud Dataflow (Apache Beam) to clean and structure incoming logs.
4. **Storage**: Centralized enterprise data warehouse using Snowflake or Google BigQuery, partitioned by borough and transaction date.
5. **ML Platform**: Scikit-Learn, XGBoost, and lightweight adapters logged via MLflow Model Registry, serving inference via FastAPI endpoints.
6. **Serving**: BI layer serving dashboard users via Streamlit, Looker, or Power BI.
7. **Governance**: Data quality checks enforced via Great Expectations, lineage monitored by OpenLineage, and infrastructure health reported in Prometheus / Grafana.

---

## 💰 Global-Scale Cost Optimization Design

A naive 50-city deployment costs **$6,810/month**. Using our five targeted optimization strategies, we reduce monthly costs by **63.4%** to **$2,490/month**:

- **AWS Spot Instances**: Offload batch ML model training workloads. **Saves $540/mo**.
- **LLM Caching & Mini Cascading**: Route 75% of simple AI queries to GPT-4o-mini and utilize a semantic database cache. **Saves $620/mo**.
- **S3 Intelligent-Tiering**: Move historical listing snapshots to low-cost archival layers. **Saves $150/mo**.
- **BigQuery flat-rate/Snowflake Auto-Suspend**: Use pre-purchased capacity reservations and suspend inactive nodes. **Saves $1,440/mo**.
- **Shared Model Serving**: Serve per-city ML models through lightweight regional adapters rather than dedicated isolated endpoints. **Saves $1,570/mo**.

---

## 🛡️ AI & Assistive Tools Disclosure

Consistent with professional guidelines, we explicitly disclose the use of artificial intelligence and automated engineering tools in the development of this platform:

1. **Code Generation & Refactoring**: Claude 3.5 Sonnet, Gemini 3.5 Flash, and GPT-4o-based agents were utilized to scaffold project components, compile ReportLab PDF tables, build unit tests, format Streamlit custom CSS, and write the dbt sql views.
2. **Data Enrichment**: Built-in mock LLM gateways and prompt templates in `src/ai_agent.py` simulate production RAG pipelines for review summarization.
3. **Validation**: Automated testing scripts verify and ensure that no hallucinated or syntactically invalid code is committed. All credentials, API keys, and personal identifier data have been excluded.
