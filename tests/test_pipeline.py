"""
tests/test_pipeline.py — Pipeline & Schema Validation Tests

Verifies that the ETL pipeline produces correctly structured,
quality-checked output in data/processed/enriched_listings.csv.

Run:
    pytest tests/test_pipeline.py -v
"""

import pytest
import pandas as pd
import numpy as np
import os
import json


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────
ENRICHED_PATH   = "data/processed/enriched_listings.csv"
METADATA_PATH   = "reports/pipeline_metadata.json"
QUALITY_REPORT  = "reports/data_quality_report.md"
PIPELINE_LOG    = "reports/pipeline.log"


@pytest.fixture(scope="module")
def enriched_df():
    """Load the enriched listings dataset once per test module."""
    if not os.path.exists(ENRICHED_PATH):
        pytest.skip(
            f"Enriched listings not found at '{ENRICHED_PATH}'. "
            "Run 'python src/pipeline.py' first."
        )
    return pd.read_csv(ENRICHED_PATH)


@pytest.fixture(scope="module")
def pipeline_metadata():
    """Load pipeline metadata JSON if available."""
    if not os.path.exists(METADATA_PATH):
        return None
    with open(METADATA_PATH) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# FILE EXISTENCE TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestOutputFilesExist:

    def test_enriched_listings_exists(self):
        """The primary enriched dataset must exist after pipeline run."""
        assert os.path.exists(ENRICHED_PATH), (
            f"'{ENRICHED_PATH}' not found. Run python src/pipeline.py"
        )

    def test_enriched_listings_nonempty(self):
        """Enriched CSV must be non-empty (> 1 KB)."""
        assert os.path.exists(ENRICHED_PATH)
        assert os.path.getsize(ENRICHED_PATH) > 1024, (
            "Enriched listings file is suspiciously small (<1KB)"
        )

    def test_pipeline_log_exists(self):
        """Pipeline should write a log file."""
        assert os.path.exists(PIPELINE_LOG), (
            f"Pipeline log not found at '{PIPELINE_LOG}'"
        )

    def test_data_quality_report_exists(self):
        """Data quality report markdown should be generated."""
        assert os.path.exists(QUALITY_REPORT), (
            f"Data quality report not found at '{QUALITY_REPORT}'"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA VALIDATION TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestSchemaValidation:

    REQUIRED_COLUMNS = [
        "id", "name", "host_id", "neighbourhood_group_cleansed",
        "latitude", "longitude", "room_type", "price",
        "minimum_nights", "number_of_reviews",
    ]

    ENRICHED_COLUMNS = [
        "occupancy_rate", "estimated_annual_revenue",
    ]

    def test_required_raw_columns_present(self, enriched_df):
        """All original Airbnb listing columns must be preserved."""
        missing = [c for c in self.REQUIRED_COLUMNS if c not in enriched_df.columns]
        assert not missing, f"Missing required columns: {missing}"

    def test_enriched_columns_present(self, enriched_df):
        """Pipeline must add enrichment columns (occupancy_rate, revenue)."""
        missing = [c for c in self.ENRICHED_COLUMNS if c not in enriched_df.columns]
        assert not missing, f"Missing enrichment columns: {missing}"

    def test_no_duplicate_listing_ids(self, enriched_df):
        """Listing IDs must be unique — duplicates indicate deduplication failure."""
        n_dupes = enriched_df["id"].duplicated().sum()
        assert n_dupes == 0, f"Found {n_dupes} duplicate listing IDs"

    def test_id_column_nonnull(self, enriched_df):
        """No listing should have a null ID."""
        n_null = enriched_df["id"].isna().sum()
        assert n_null == 0, f"{n_null} rows have null 'id'"


# ─────────────────────────────────────────────────────────────────────────────
# DATA QUALITY TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestDataQuality:

    def test_minimum_row_count(self, enriched_df):
        """Enriched dataset must contain at least 1,000 listings (sanity check)."""
        assert len(enriched_df) >= 1000, (
            f"Dataset has only {len(enriched_df)} rows — expected 1,000+"
        )

    def test_price_no_negatives(self, enriched_df):
        """Prices must be non-negative — negative values indicate cleaning failure."""
        n_negative = (enriched_df["price"] < 0).sum()
        assert n_negative == 0, f"{n_negative} listings have negative prices"

    def test_price_no_zeros(self, enriched_df):
        """Zero-price listings should have been filtered during cleaning."""
        n_zero = (enriched_df["price"] == 0).sum()
        assert n_zero == 0, (
            f"{n_zero} listings have $0 price — expected these to be cleaned out"
        )

    def test_price_reasonable_ceiling(self, enriched_df):
        """Prices above $35,000/night are likely data quality issues."""
        n_extreme = (enriched_df["price"] > 35_000).sum()
        assert n_extreme == 0, (
            f"{n_extreme} listings have price > $35,000 — check outlier cleaning"
        )

    def test_latitude_valid_range(self, enriched_df):
        """Latitude values must be within NYC bounds (approx 40.4–41.0)."""
        invalid = enriched_df[
            (enriched_df["latitude"] < 40.4) | (enriched_df["latitude"] > 41.0)
        ]
        assert len(invalid) == 0, (
            f"{len(invalid)} listings have latitude outside NYC bounds"
        )

    def test_longitude_valid_range(self, enriched_df):
        """Longitude values must be within NYC bounds (approx -74.3 to -73.7)."""
        invalid = enriched_df[
            (enriched_df["longitude"] < -74.3) | (enriched_df["longitude"] > -73.7)
        ]
        assert len(invalid) == 0, (
            f"{len(invalid)} listings have longitude outside NYC bounds"
        )

    def test_room_type_valid_values(self, enriched_df):
        """Room type must be one of the known Airbnb categories."""
        valid_room_types = {
            "Entire Home/Apt", "Private Room",
            "Shared Room", "Hotel Room"
        }
        actual = set(enriched_df["room_type"].dropna().unique())
        invalid = actual - valid_room_types
        assert not invalid, f"Unexpected room_type values: {invalid}"

    def test_null_rate_price_below_threshold(self, enriched_df):
        """Null rate for 'price' column must be below 5%."""
        null_rate = enriched_df["price"].isna().mean()
        assert null_rate < 0.05, (
            f"Price null rate is {null_rate:.1%} — exceeds 5% threshold"
        )

    def test_null_rate_room_type_below_threshold(self, enriched_df):
        """Null rate for 'room_type' must be below 2%."""
        null_rate = enriched_df["room_type"].isna().mean()
        assert null_rate < 0.02, (
            f"room_type null rate is {null_rate:.1%} — exceeds 2% threshold"
        )

    def test_borough_values(self, enriched_df):
        """All boroughs must be valid NYC boroughs."""
        valid_boroughs = {
            "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"
        }
        actual = set(enriched_df["neighbourhood_group_cleansed"].dropna().unique())
        invalid = actual - valid_boroughs
        assert not invalid, f"Unknown borough values: {invalid}"

    def test_minimum_nights_positive(self, enriched_df):
        """minimum_nights must be a positive integer — 0 or negative is invalid."""
        n_invalid = (enriched_df["minimum_nights"] <= 0).sum()
        assert n_invalid == 0, (
            f"{n_invalid} listings have minimum_nights <= 0"
        )

    def test_occupancy_rate_bounded(self, enriched_df):
        """Occupancy rate must be between 0 and 1 (inclusive)."""
        if "occupancy_rate" not in enriched_df.columns:
            pytest.skip("occupancy_rate column not present")
        invalid = enriched_df[
            (enriched_df["occupancy_rate"] < 0) |
            (enriched_df["occupancy_rate"] > 1)
        ]
        assert len(invalid) == 0, (
            f"{len(invalid)} listings have occupancy_rate outside [0, 1]"
        )

    def test_estimated_revenue_nonnegative(self, enriched_df):
        """Annual revenue estimate must be non-negative."""
        if "estimated_annual_revenue" not in enriched_df.columns:
            pytest.skip("estimated_annual_revenue column not present")
        n_negative = (enriched_df["estimated_annual_revenue"] < 0).sum()
        assert n_negative == 0, (
            f"{n_negative} listings have negative estimated_annual_revenue"
        )


# ─────────────────────────────────────────────────────────────────────────────
# BOROUGH DISTRIBUTION TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestBoroughDistribution:

    def test_all_five_boroughs_present(self, enriched_df):
        """All 5 NYC boroughs must be represented in the dataset."""
        expected_boroughs = {
            "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"
        }
        actual_boroughs = set(
            enriched_df["neighbourhood_group_cleansed"].dropna().unique()
        )
        missing = expected_boroughs - actual_boroughs
        assert not missing, f"Missing boroughs: {missing}"

    def test_manhattan_is_largest_borough(self, enriched_df):
        """Manhattan typically has the most Airbnb listings in NYC."""
        counts = enriched_df["neighbourhood_group_cleansed"].value_counts()
        top_borough = counts.index[0]
        # Allow Manhattan or Brooklyn (both commonly #1)
        assert top_borough in {"Manhattan", "Brooklyn"}, (
            f"Expected Manhattan or Brooklyn as largest borough, got '{top_borough}'"
        )

    def test_no_single_borough_dominates(self, enriched_df):
        """No single borough should contain >70% of all listings."""
        counts = enriched_df["neighbourhood_group_cleansed"].value_counts(normalize=True)
        max_share = counts.iloc[0]
        assert max_share < 0.70, (
            f"Borough '{counts.index[0]}' has {max_share:.0%} of listings — "
            "unexpected concentration"
        )
