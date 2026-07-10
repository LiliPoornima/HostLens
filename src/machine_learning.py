import os
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, mean_absolute_percentage_error
from sklearn.preprocessing import StandardScaler

# Lexicon of positive and negative words for fast sentiment analysis
POSITIVE_WORDS = {
    "great", "excellent", "wonderful", "perfect", "clean", "beautiful", "quiet", "comfortable",
    "love", "loved", "nice", "friendly", "helpful", "convenient", "easy", "cozy", "spacious",
    "amazing", "best", "good", "happy", "pleased", "recommend", "host", "location", "awesome",
    "definitely", "highly", "super", "fantastic", "peaceful", "safe", "smooth", "spotless"
}

NEGATIVE_WORDS = {
    "dirty", "noisy", "bad", "terrible", "poor", "unclean", "rude", "loud", "small", "expensive",
    "broken", "cold", "smell", "smelly", "disappointed", "worst", "hate", "uncomfortable",
    "issues", "problem", "difficult", "leak", "bugs", "bug", "roach", "roaches", "mice",
    "old", "dusty", "thin", "walls", "light", "cancelled", "cancel", "refund", "charging"
}

def calculate_lexicon_sentiment(text):
    if not isinstance(text, str):
        return 0.0
    words = text.lower().split()
    if not words:
        return 0.0
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    score = (pos_count - neg_count) / len(words)
    return float(score * 10) # scale to -10 to +10 range

def run_ml_and_sentiment():
    print("Starting Machine Learning & NLP analysis...")
    os.makedirs("reports", exist_ok=True)

    # Load data
    df = pd.read_csv("data/processed/enriched_listings.csv")
    reviews = pd.read_csv("data/processed/reviews_cleaned.csv")
    
    # 1. Sentiment Analysis on Reviews
    print("Running sentiment analysis on reviews...")
    # Sample 100k reviews for speed
    reviews_sample = reviews.dropna(subset=["comments"]).sample(n=min(100000, len(reviews)), random_state=42).copy()
    reviews_sample["sentiment_score"] = reviews_sample["comments"].apply(calculate_lexicon_sentiment)
    
    # Group sentiment by listing
    listing_sentiment = reviews_sample.groupby("listing_id")["sentiment_score"].mean().reset_index(name="avg_review_sentiment")
    
    # Merge back to listings
    df = df.merge(listing_sentiment, left_on="id", right_on="listing_id", how="left").drop(columns=["listing_id"], errors="ignore")
    # Impute missing sentiment with 0 (neutral)
    df["avg_review_sentiment"] = df["avg_review_sentiment"].fillna(0.0)
    
    # Persist the sentiment column back to enriched_listings.csv so the dashboard can read it
    df.to_csv("data/processed/enriched_listings.csv", index=False)
    print("Saved sentiment-enriched listings to data/processed/enriched_listings.csv")
    
    # Correlate sentiment with rating scores
    sentiment_rating_corr = float(df[["avg_review_sentiment", "review_scores_rating"]].corr().iloc[0, 1])
    print(f"Sentiment-Rating Correlation: {sentiment_rating_corr:.4f}")

    # 2. Machine Learning Pricing Model
    print("Preparing features for pricing prediction...")
    
    # Select features
    ml_cols = [
        "price", "bedrooms", "beds", "room_type", "neighbourhood_group_cleansed",
        "review_scores_rating", "host_is_superhost", "number_of_reviews"
    ]
    ml_df = df[ml_cols].dropna().copy()
    
    # Text length proxy features from main df
    ml_df["name_len"] = df.loc[ml_df.index, "name"].fillna("").astype(str).str.len()
    ml_df["desc_len"] = df.loc[ml_df.index, "description"].fillna("").astype(str).str.len()
    
    # Target variable log-transform
    ml_df["log_price"] = np.log1p(ml_df["price"])
    ml_df["host_is_superhost"] = ml_df["host_is_superhost"].map({"t": 1, "f": 0}).fillna(0)
    
    # Categorical variables encoding
    ml_df = pd.get_dummies(ml_df, columns=["room_type", "neighbourhood_group_cleansed"], drop_first=True)
    
    # Split features and target
    X = ml_df.drop(columns=["price", "log_price"])
    y_log = ml_df["log_price"]
    y_orig = ml_df["price"]
    
    # Standardize numerical features
    num_features = ["bedrooms", "beds", "review_scores_rating", "number_of_reviews", "name_len", "desc_len"]
    scaler = StandardScaler()
    X_scaled = X.copy()
    X_scaled[num_features] = scaler.fit_transform(X[num_features])
    
    # Cross validation setup
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    models = {
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=50, max_depth=12, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, max_depth=6, random_state=42)
    }
    
    model_results = {}
    
    for name, model in models.items():
        print(f"Training {name}...")
        mae_list, rmse_list, mape_list = [], [], []
        
        for train_idx, test_idx in kf.split(X_scaled):
            X_train, X_test = X_scaled.iloc[train_idx], X_scaled.iloc[test_idx]
            y_train, y_test = y_log.iloc[train_idx], y_log.iloc[test_idx]
            y_test_orig = y_orig.iloc[test_idx]
            
            # Fit model
            model.fit(X_train, y_train)
            
            # Predict log-price
            pred_log = model.predict(X_test)
            
            # Convert back to original price scale
            pred_orig = np.expm1(pred_log)
            # Clip negative predictions to 0
            pred_orig = np.clip(pred_orig, 0, None)
            
            # Compute metrics
            mae = mean_absolute_error(y_test_orig, pred_orig)
            rmse = root_mean_squared_error(y_test_orig, pred_orig)
            mape = mean_absolute_percentage_error(y_test_orig, pred_orig)
            
            mae_list.append(mae)
            rmse_list.append(rmse)
            mape_list.append(mape)
            
        model_results[name] = {
            "MAE": float(np.mean(mae_list)),
            "RMSE": float(np.mean(rmse_list)),
            "MAPE": float(np.mean(mape_list))
        }
        print(f"{name} Results - MAE: {np.mean(mae_list):.2f}, RMSE: {np.mean(rmse_list):.2f}, MAPE: {np.mean(mape_list)*100:.2f}%")

    # Fit a final Random Forest to extract feature importances
    rf_final = RandomForestRegressor(n_estimators=50, max_depth=12, random_state=42, n_jobs=-1)
    rf_final.fit(X_scaled, y_log)
    
    feat_importances = pd.DataFrame({
        "feature": X.columns,
        "importance": rf_final.feature_importances_
    }).sort_values(by="importance", ascending=False)
    
    feat_importances.to_csv("reports/feature_importances.csv", index=False)

    # Save summary report of ML and sentiment findings
    summary = {
        "sentiment_analysis": {
            "review_sample_size": len(reviews_sample),
            "sentiment_rating_correlation": sentiment_rating_corr,
            "interpretation": "Positive correlation indicates reviews with cleaner, better hosts command higher rating scores."
        },
        "price_prediction_models": model_results
    }
    
    with open("reports/ml_findings.json", "w") as f:
        json.dump(summary, f, indent=4)
        
    print("Machine Learning & NLP analysis complete. Output saved.")

if __name__ == "__main__":
    run_ml_and_sentiment()
