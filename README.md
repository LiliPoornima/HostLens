# HostLens# HostLens

HostLens is an end-to-end data engineering and analytics platform built using the Inside Airbnb dataset. The project transforms raw Airbnb listings, reviews, and calendar data into analytics-ready datasets through ingestion, cleaning, enrichment, statistical analysis, and dimensional modeling.

## Project Objectives

- Explore and profile Airbnb datasets.
- Clean and standardize raw data.
- Build enriched analytical datasets.
- Perform exploratory data analysis.
- Conduct statistical hypothesis testing.
- Design a star schema for analytical workloads.
- Create SQL queries for business insights.

## Dataset

This project uses the Inside Airbnb dataset for New York City.

Datasets used:

- `listings.csv`
- `calendar.csv`
- `reviews.csv`
- `neighbourhoods.csv`

Source:

https://insideairbnb.com/get-the-data/

## Project Structure

```text
HostLens/

├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── 01_dataset_exploration.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_data_enrichment.ipynb
│   ├── 04_eda.ipynb
│   ├── 05_statistical_analysis.ipynb
│   └── 06_data_modeling.ipynb
│
├── sql/
│   ├── schema.sql
│   └── analytics_queries.sql
│
├── reports/
├── src/
│
├── README.md
├── requirements.txt
└── .gitignore
```

## Technologies

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- SciPy
- DuckDB
- SQL
- Jupyter Notebook

## Key Analyses

### Exploratory Data Analysis

- Price distribution analysis
- Room type comparison
- Host portfolio analysis
- Review and demand analysis
- Correlation analysis

### Statistical Analysis

Hypotheses tested:

1. Do entire homes cost more than private rooms?
2. Do superhosts receive higher ratings?
3. Do superhosts charge different prices?

### Data Modeling

A star schema was designed with:

Dimension tables:

- `dim_hosts`
- `dim_neighbourhoods`
- `dim_property`
- `dim_reviews`

Fact table:

- `fact_listings`

## Setup

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/HostLens.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch Jupyter:

```bash
jupyter notebook
```

## Future Improvements

- Interactive dashboard development
- Occupancy and seasonality analysis
- Machine learning models for price prediction
- Data pipeline automation

## Author

Poornima Liyanage

BSc (Hons) in Information Technology (Data Science)
