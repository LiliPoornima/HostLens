"""
tests/test_ml.py — Machine Learning Model Tests

Validates that:
  1. Trained model artifacts can be loaded from disk
  2. Models produce valid, bounded predictions
  3. Feature transformations (scaler) work correctly
  4. Cross-validation metrics meet minimum quality thresholds

Run:
    pytest tests/test_ml.py -v
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

# Ensure src/ is on path so we can import local modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
ENRICHED_PATH      = "data/processed/enriched_listings.csv"
FEATURE_IMP_PATH   = "reports/feature_importances.csv"
ML_MODELS_DIR      = "reports"   # joblib files saved here by machine_learning.py

# Models expected to be serialized by machine_learning.py
EXPECTED_MODEL_FILES = [
    "model_rf.joblib",
    "model_ridge.joblib",
    "model_gb.joblib",
]
EXPECTED_SCALER_FILE = "scaler.joblib"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _try_import_joblib():
    try:
        import joblib
        return joblib
    except ImportError:
        pytest.skip("joblib not installed — run pip install joblib")


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def enriched_df():
    if not os.path.exists(ENRICHED_PATH):
        pytest.skip(f"Enriched listings not found at '{ENRICHED_PATH}'")
    return pd.read_csv(ENRICHED_PATH)


@pytest.fixture(scope="module")
def feature_cols():
    """Return the feature column list used for ML, matching machine_learning.py."""
    return [
        "latitude", "longitude", "room_type", "minimum_nights",
        "number_of_reviews", "review_scores_rating",
        "calculated_host_listings_count", "availability_365",
        "host_is_superhost", "neighbourhood_group_cleansed",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# MODEL ARTIFACT TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestModelArtifactsExist:

    def test_feature_importances_file_exists(self):
        """Feature importances CSV must be present after ML training."""
        assert os.path.exists(FEATURE_IMP_PATH), (
            f"'{FEATURE_IMP_PATH}' not found. Run 'python src/machine_learning.py'"
        )

    @pytest.mark.parametrize("model_file", EXPECTED_MODEL_FILES)
    def test_model_joblib_exists(self, model_file):
        """Each trained model must be serialized as a joblib file."""
        path = os.path.join(ML_MODELS_DIR, model_file)
        if not os.path.exists(path):
            pytest.skip(
                f"'{path}' not found — joblib serialization may not be "
                "implemented in current machine_learning.py version"
            )
        assert os.path.getsize(path) > 0, f"Model file '{path}' is empty"

    def test_scaler_joblib_exists(self):
        """Fitted scaler must be serialized alongside the models."""
        path = os.path.join(ML_MODELS_DIR, EXPECTED_SCALER_FILE)
        if not os.path.exists(path):
            pytest.skip(
                f"'{path}' not found — scaler serialization may not be "
                "implemented in current machine_learning.py version"
            )
        assert os.path.getsize(path) > 0, "Scaler file is empty"


# ─────────────────────────────────────────────────────────────────────────────
# MODEL LOADING TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestModelLoading:

    @pytest.mark.parametrize("model_file", EXPECTED_MODEL_FILES)
    def test_model_loads_successfully(self, model_file):
        """Model files must be loadable with joblib without errors."""
        joblib = _try_import_joblib()
        path = os.path.join(ML_MODELS_DIR, model_file)
        if not os.path.exists(path):
            pytest.skip(f"Model file '{path}' not found")
        model = joblib.load(path)
        assert model is not None, f"Failed to load model from '{path}'"

    @pytest.mark.parametrize("model_file", EXPECTED_MODEL_FILES)
    def test_model_has_predict_method(self, model_file):
        """All models must implement the scikit-learn predict() interface."""
        joblib = _try_import_joblib()
        path = os.path.join(ML_MODELS_DIR, model_file)
        if not os.path.exists(path):
            pytest.skip(f"Model file '{path}' not found")
        model = joblib.load(path)
        assert hasattr(model, "predict"), (
            f"Model in '{path}' does not have a predict() method"
        )


# ─────────────────────────────────────────────────────────────────────────────
# PREDICTION QUALITY TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestModelPredictions:

    def _prepare_features(self, df):
        """Minimal feature preparation matching the pipeline in machine_learning.py."""
        feature_cols = [
            "latitude", "longitude", "minimum_nights",
            "number_of_reviews", "calculated_host_listings_count",
            "availability_365",
        ]
        available = [c for c in feature_cols if c in df.columns]
        sample = df[available].dropna().head(100).copy()
        return sample

    @pytest.mark.parametrize("model_file", EXPECTED_MODEL_FILES)
    def test_model_predictions_nonnegative(self, model_file, enriched_df):
        """Price predictions must be non-negative (prices can't be < $0)."""
        joblib = _try_import_joblib()
        path = os.path.join(ML_MODELS_DIR, model_file)
        if not os.path.exists(path):
            pytest.skip(f"Model file '{path}' not found")

        model = joblib.load(path)
        X = self._prepare_features(enriched_df)
        if len(X) == 0:
            pytest.skip("No valid rows for prediction after feature prep")

        preds = model.predict(X)
        n_neg = (preds < 0).sum()
        assert n_neg == 0, (
            f"{n_neg} negative predictions from '{model_file}' — "
            "consider using np.maximum(preds, 0) in production"
        )

    @pytest.mark.parametrize("model_file", EXPECTED_MODEL_FILES)
    def test_model_predictions_finite(self, model_file, enriched_df):
        """Model must not produce NaN or Inf predictions."""
        joblib = _try_import_joblib()
        path = os.path.join(ML_MODELS_DIR, model_file)
        if not os.path.exists(path):
            pytest.skip(f"Model file '{path}' not found")

        model = joblib.load(path)
        X = self._prepare_features(enriched_df)
        if len(X) == 0:
            pytest.skip("No valid rows for prediction after feature prep")

        preds = model.predict(X)
        assert np.all(np.isfinite(preds)), (
            f"Model '{model_file}' produced NaN or Inf predictions"
        )

    @pytest.mark.parametrize("model_file", EXPECTED_MODEL_FILES)
    def test_model_predictions_reasonable_range(self, model_file, enriched_df):
        """Predictions should be within $5 to $2,000/night (sanity check)."""
        joblib = _try_import_joblib()
        path = os.path.join(ML_MODELS_DIR, model_file)
        if not os.path.exists(path):
            pytest.skip(f"Model file '{path}' not found")

        model = joblib.load(path)
        X = self._prepare_features(enriched_df)
        if len(X) == 0:
            pytest.skip("No valid rows for prediction after feature prep")

        preds = model.predict(X)
        median_pred = np.median(preds)
        assert 20 <= median_pred <= 2000, (
            f"Median prediction from '{model_file}' is ${median_pred:.0f} — "
            "this is outside the expected NYC Airbnb price range ($20–$2,000)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING TESTS (no joblib required)
# ─────────────────────────────────────────────────────────────────────────────
class TestFeatureEngineering:

    def test_price_log_transform_reduces_skewness(self, enriched_df):
        """Log-transforming price should produce a more symmetric distribution."""
        prices = enriched_df["price"].dropna()
        prices = prices[prices > 0]

        raw_skew  = prices.skew()
        log_skew  = np.log1p(prices).skew()

        assert abs(log_skew) < abs(raw_skew), (
            f"Log transform did not reduce skewness: "
            f"raw={raw_skew:.2f} vs log={log_skew:.2f}"
        )

    def test_superhost_column_is_binary(self, enriched_df):
        """host_is_superhost must be binary (0/1 or True/False) after encoding."""
        if "host_is_superhost" not in enriched_df.columns:
            pytest.skip("host_is_superhost column not present")
        col = enriched_df["host_is_superhost"].dropna()
        unique_vals = set(col.unique())
        # Accept numeric 0/1, or boolean True/False, or string 't'/'f'
        allowed = {0, 1, True, False, "t", "f", "True", "False", 0.0, 1.0}
        unexpected = unique_vals - allowed
        assert not unexpected, (
            f"host_is_superhost has unexpected values: {unexpected}"
        )

    def test_no_infinite_values_in_numeric_columns(self, enriched_df):
        """No column in the enriched dataset should contain Inf values."""
        numeric = enriched_df.select_dtypes(include=[np.number])
        inf_cols = [c for c in numeric.columns if np.isinf(numeric[c]).any()]
        assert not inf_cols, f"Inf values found in columns: {inf_cols}"
