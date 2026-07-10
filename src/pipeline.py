import os
import sys
import logging
import json
from datetime import datetime
import pandas as pd
import numpy as np
import duckdb
from rapidfuzz import fuzz

# Setup logging
os.makedirs("reports", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("reports/pipeline.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HostLensETL")

def run_pipeline():
    logger.info("Starting HostLens end-to-end pipeline...")

    raw_path = "data/raw"
    processed_path = "data/processed"
    os.makedirs(processed_path, exist_ok=True)

    # 1. Ingestion
    logger.info("Step 1: Loading raw datasets...")
    try:
        listings_raw = pd.read_csv(f"{raw_path}/listings.csv")
        calendar_raw = pd.read_csv(f"{raw_path}/calendar.csv")
        reviews_raw = pd.read_csv(f"{raw_path}/reviews.csv")
        neighbourhoods_raw = pd.read_csv(f"{raw_path}/neighbourhoods.csv")
        
        logger.info(f"Loaded Listings: {listings_raw.shape[0]} rows, {listings_raw.shape[1]} cols")
        logger.info(f"Loaded Calendar: {calendar_raw.shape[0]} rows, {calendar_raw.shape[1]} cols")
        logger.info(f"Loaded Reviews: {reviews_raw.shape[0]} rows, {reviews_raw.shape[1]} cols")
        logger.info(f"Loaded Neighbourhoods: {neighbourhoods_raw.shape[0]} rows, {neighbourhoods_raw.shape[1]} cols")
    except Exception as e:
        logger.error(f"Error loading datasets: {e}")
        sys.exit(1)

    # 2. Ingestion & Profiling Report
    logger.info("Step 2: Profiling raw datasets...")
    profiling_rows = []
    for name, df in [("listings", listings_raw), ("calendar", calendar_raw), 
                     ("reviews", reviews_raw), ("neighbourhoods", neighbourhoods_raw)]:
        null_counts = df.isnull().sum()
        null_pct = df.isnull().mean() * 100
        cardinality = df.nunique()
        dtypes = df.dtypes.astype(str)
        
        profile_df = pd.DataFrame({
            "dataset": name,
            "column": df.columns,
            "dtype": dtypes,
            "null_count": null_counts,
            "null_pct": null_pct,
            "cardinality": cardinality
        })
        profiling_rows.append(profile_df)
    
    profile_summary = pd.concat(profiling_rows)
    profile_summary.to_csv("reports/data_profiling_summary.csv", index=False)
    logger.info("Saved reports/data_profiling_summary.csv")

    # Detect duplicate records deterministically
    logger.info("Detecting duplicate records...")
    dup_listings_exact = listings_raw.duplicated(subset=["id"]).sum()
    logger.info(f"Found {dup_listings_exact} exact duplicates in Listings by ID.")

    # Fuzzy duplicate matching on a sample of names
    logger.info("Running fuzzy duplicate detection on listings names (sample)...")
    names_sample = listings_raw["name"].dropna().drop_duplicates().head(200).tolist()
    fuzzy_matches = []
    for i in range(len(names_sample)):
        for j in range(i + 1, len(names_sample)):
            score = fuzz.ratio(str(names_sample[i]).lower(), str(names_sample[j]).lower())
            if score >= 85:
                fuzzy_matches.append((names_sample[i], names_sample[j], score))
    logger.info(f"Fuzzy duplicate check completed. Found {len(fuzzy_matches)} highly similar names in sample.")

    # 3. Data Cleaning
    logger.info("Step 3: Cleaning datasets...")
    listings = listings_raw.copy()
    calendar = calendar_raw.copy()
    reviews = reviews_raw.copy()

    # Drop duplicate rows by ID
    listings.drop_duplicates(subset=["id"], inplace=True)
    reviews.drop_duplicates(subset=["id"], inplace=True)
    calendar.drop_duplicates(subset=["listing_id", "date"], inplace=True)

    # Standardize price
    logger.info("Standardizing pricing fields...")
    for col in ["price"]:
        listings[col] = listings[col].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False)
        listings[col] = pd.to_numeric(listings[col], errors="coerce")
    
    # Fill price missing values with median price
    median_price = listings["price"].median()
    listings["price"] = listings["price"].fillna(median_price)
    
    # Filter listings with valid coordinates and pricing
    listings = listings[
        (listings["price"] >= 0) &
        (listings["latitude"].between(-90, 90)) &
        (listings["longitude"].between(-180, 180))
    ]

    # Standardize date fields
    logger.info("Standardizing date columns...")
    listings["last_scraped"] = pd.to_datetime(listings["last_scraped"], errors="coerce")
    listings["host_since"] = pd.to_datetime(listings["host_since"], errors="coerce")
    calendar["date"] = pd.to_datetime(calendar["date"], errors="coerce")
    reviews["date"] = pd.to_datetime(reviews["date"], errors="coerce")

    # Normalize categorical columns
    logger.info("Normalizing room and property types...")
    listings["room_type"] = listings["room_type"].astype(str).str.strip().str.title()
    listings["property_type"] = listings["property_type"].astype(str).str.strip().str.title()
    listings["neighbourhood_cleansed"] = listings["neighbourhood_cleansed"].astype(str).str.strip().str.title()
    listings["neighbourhood_group_cleansed"] = listings["neighbourhood_group_cleansed"].astype(str).str.strip().str.title()

    # Impute missing values
    listings["bedrooms"] = listings["bedrooms"].fillna(listings["bedrooms"].median())
    listings["beds"] = listings["beds"].fillna(listings["beds"].median())
    listings["review_scores_rating"] = listings["review_scores_rating"].fillna(listings["review_scores_rating"].median())
    listings["reviews_per_month"] = listings["reviews_per_month"].fillna(0.0)

    # 4. Data Enrichment
    logger.info("Step 4: Enriching datasets...")
    
    # Review aggregation by listing
    logger.info("Aggregating reviews...")
    review_counts = reviews.groupby("listing_id").size().reset_index(name="review_count_reviews_file")
    first_last_reviews = reviews.groupby("listing_id").agg(
        first_review_date=("date", "min"),
        last_review_date=("date", "max")
    ).reset_index()
    
    # Integrate calendar data to compute occupancy and estimated revenue
    logger.info("Integrating calendar availability and computing occupancy rate...")
    # 'f' in calendar represents booked, 't' represents available.
    calendar["is_booked"] = calendar["available"].map({"f": 1, "t": 0})
    calendar_agg = calendar.groupby("listing_id").agg(
        total_days=("date", "count"),
        booked_days=("is_booked", "sum")
    ).reset_index()
    
    calendar_agg["occupancy_rate"] = calendar_agg["booked_days"] / calendar_agg["total_days"].replace(0, np.nan)
    calendar_agg["occupancy_rate"] = calendar_agg["occupancy_rate"].fillna(0.0)
    
    # Join enrichments with listings
    listings = listings.merge(review_counts, left_on="id", right_on="listing_id", how="left").drop(columns=["listing_id"], errors="ignore")
    listings = listings.merge(first_last_reviews, left_on="id", right_on="listing_id", how="left").drop(columns=["listing_id"], errors="ignore")
    listings = listings.merge(calendar_agg, left_on="id", right_on="listing_id", how="left").drop(columns=["listing_id"], errors="ignore")
    
    # Compute revenue estimates
    listings["occupancy_rate"] = listings["occupancy_rate"].fillna(0.0)
    listings["estimated_annual_revenue"] = listings["price"] * (listings["occupancy_rate"] * 365)

    # Compute host tenure in years based on last scraped date
    listings["host_tenure_years"] = (listings["last_scraped"] - listings["host_since"]).dt.days / 365.25
    listings["host_tenure_years"] = listings["host_tenure_years"].fillna(0.0)

    # Compute price per bedroom (handle 0 bedrooms case)
    listings["price_per_bedroom"] = listings["price"] / listings["bedrooms"].replace(0, 1)

    # Compute review frequency (reviews per year on platform)
    listings["review_frequency_annual"] = listings["number_of_reviews"] / listings["host_tenure_years"].replace(0, 1)
    
    # Neighborhood averages (median price, listing density, average rating)
    logger.info("Computing neighbourhood-level aggregates...")
    neigh_agg = listings.groupby("neighbourhood_cleansed").agg(
        neigh_median_price=("price", "median"),
        neigh_listing_count=("id", "count"),
        neigh_avg_rating=("review_scores_rating", "mean")
    ).reset_index()
    
    listings = listings.merge(neigh_agg, on="neighbourhood_cleansed", how="left")
    
    # Save cleaned and enriched outputs
    listings.to_csv(f"{processed_path}/listings_cleaned.csv", index=False)
    listings.to_csv(f"{processed_path}/enriched_listings.csv", index=False)
    reviews.to_csv(f"{processed_path}/reviews_cleaned.csv", index=False)
    logger.info("Saved cleaned and enriched CSV files.")

    # 5. Data Modeling and DuckDB Load
    logger.info("Step 5: Setting up DuckDB and loading tables...")
    db_file = f"{processed_path}/hostlens.db"
    
    # If file exists, remove to reload schema fresh
    if os.path.exists(db_file):
        os.remove(db_file)
        logger.info("Cleared existing DuckDB file.")

    conn = duckdb.connect(db_file)
    
    # Read and execute schema.sql
    try:
        with open("sql/schema.sql", "r") as f:
            schema_sql = f.read()
        
        # Execute schema DDL statements
        # Since standard DuckDB might run multiple statements, split by semicolon
        statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
        for stmt in statements:
            conn.execute(stmt)
        logger.info("Initialized database schema.")
    except Exception as e:
        logger.error(f"Error executing schema.sql: {e}")
        conn.close()
        sys.exit(1)

    # Prepare data for dimension and fact tables
    # 1. dim_hosts
    df_hosts_pd = listings[["host_id", "host_name", "host_is_superhost", "host_location"]].drop_duplicates(subset=["host_id"])
    df_hosts_pd["host_name"] = df_hosts_pd["host_name"].fillna("Unknown Host")
    df_hosts_pd["host_is_superhost"] = df_hosts_pd["host_is_superhost"].fillna("f")
    df_hosts_pd["host_location"] = df_hosts_pd["host_location"].fillna("Unknown Location")
    
    # 2. dim_neighbourhoods
    df_neigh_pd = listings[["neighbourhood_cleansed", "neighbourhood_group_cleansed"]].drop_duplicates(subset=["neighbourhood_cleansed"])
    
    # 3. dim_property
    df_prop_pd = listings[["id", "property_type", "room_type", "bedrooms", "beds"]].rename(columns={"id": "listing_id"})
    
    # 4. dim_reviews
    # Format dates as string for SQL insert compatibility if needed
    df_rev_pd = listings[["id", "first_review_date", "last_review_date"]].rename(
        columns={"id": "listing_id", "first_review_date": "first_review", "last_review_date": "last_review"}
    )
    df_rev_pd["first_review"] = pd.to_datetime(df_rev_pd["first_review"]).dt.strftime('%Y-%m-%d')
    df_rev_pd["last_review"] = pd.to_datetime(df_rev_pd["last_review"]).dt.strftime('%Y-%m-%d')
    
    # 5. fact_listings
    df_list_pd = listings[[
        "id", "host_id", "neighbourhood_cleansed", "price", 
        "number_of_reviews", "review_scores_rating", "reviews_per_month"
    ]].rename(columns={"id": "listing_id"})
    
    # Use total reviews aggregated from review_counts as total_reviews metric
    review_counts_map = review_counts.set_index("listing_id")["review_count_reviews_file"].to_dict()
    df_list_pd["total_reviews"] = df_list_pd["listing_id"].map(review_counts_map).fillna(0).astype(int)

    # Insert dataframes directly into DuckDB tables using DuckDB's integration with Pandas
    conn.execute("INSERT INTO dim_hosts SELECT * FROM df_hosts_pd")
    conn.execute("INSERT INTO dim_neighbourhoods SELECT * FROM df_neigh_pd")
    conn.execute("INSERT INTO dim_property SELECT * FROM df_prop_pd")
    conn.execute("INSERT INTO dim_reviews SELECT * FROM df_rev_pd")
    conn.execute("INSERT INTO fact_listings SELECT * FROM df_list_pd")
    
    logger.info("Successfully loaded data into DuckDB tables.")
    
    # Run test verification
    row_count = conn.execute("SELECT COUNT(*) FROM fact_listings").fetchone()[0]
    logger.info(f"Verification: fact_listings has {row_count} rows loaded.")
    
    # Ingest pipeline run metadata
    run_timestamp = datetime.now()
    run_id = f"run_{run_timestamp.strftime('%Y%m%d_%H%M%S')}"
    metadata = {
        "run_id": run_id,
        "run_timestamp": run_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "listings_raw_count": int(listings_raw.shape[0]),
        "calendar_raw_count": int(calendar_raw.shape[0]),
        "reviews_raw_count": int(reviews_raw.shape[0]),
        "listings_cleaned_count": int(listings.shape[0]),
        "duplicate_listings_count": int(dup_listings_exact),
        "fuzzy_matches_count": int(len(fuzzy_matches)),
        "status": "SUCCESS"
    }
    
    # Save as JSON file
    with open("reports/pipeline_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    logger.info("Saved pipeline run metrics to reports/pipeline_metadata.json")
    
    # Load metadata df and write to metadata_log
    df_meta_pd = pd.DataFrame([metadata])
    df_meta_pd["run_timestamp"] = pd.to_datetime(df_meta_pd["run_timestamp"])
    conn.execute("INSERT INTO metadata_log SELECT * FROM df_meta_pd")
    logger.info("Successfully inserted execution telemetry into DuckDB metadata_log.")

    conn.close()
    logger.info("ETL pipeline execution complete! Success.")

if __name__ == "__main__":
    run_pipeline()
