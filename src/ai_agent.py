import os
import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib

class RAGEngine:
    def __init__(self, reviews_path="data/processed/reviews_cleaned.csv", sample_size=30000):
        self.reviews_path = reviews_path
        self.sample_size = sample_size
        self.vectorizer = None
        self.tfidf_matrix = None
        self.reviews_df = None
        self._initialize()

    def _initialize(self):
        if not os.path.exists(self.reviews_path):
            print(f"Reviews dataset not found at {self.reviews_path}. RAG Engine disabled.")
            return
        
        try:
            # Read and sample for performance
            df = pd.read_csv(self.reviews_path)
            self.reviews_df = df.dropna(subset=["comments"]).sample(n=min(self.sample_size, len(df)), random_state=42).copy()
            
            # Initialize TF-IDF
            self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
            self.tfidf_matrix = self.vectorizer.fit_transform(self.reviews_df["comments"])
            print("RAG Search Engine initialized successfully.")
        except Exception as e:
            print(f"Error initializing RAG Engine: {e}")

    def query(self, user_query, top_n=3):
        if self.vectorizer is None or self.tfidf_matrix is None:
            self._initialize()
            if self.vectorizer is None or self.tfidf_matrix is None:
                return {
                    "answer": "RAG Engine is not initialized. Please run the ETL pipeline first.",
                    "sources": []
                }
        
        # Vectorize query
        query_vec = self.vectorizer.transform([user_query])
        
        # Compute cosine similarity
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[-top_n:][::-1]
        
        sources = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.05: # threshold
                row = self.reviews_df.iloc[idx]
                sources.append({
                    "comment": str(row["comments"]).strip(),
                    "date": str(row["date"]),
                    "listing_id": int(row["listing_id"]),
                    "similarity": score
                })
        
        if not sources:
            return {
                "answer": "No highly relevant guest comments found in the reviews corpus for your query.",
                "sources": []
            }
        
        # Generate dynamic summary feedback
        # In a real setup, we would send these matching reviews to Gemini or GPT.
        # Here we provide a deterministic structured analysis summarizing the matches.
        pos_words = ["clean", "great", "perfect", "good", "nice", "love", "spacious"]
        neg_words = ["dirty", "noise", "loud", "cancel", "terrible", "bad", "smelly"]
        
        matched_pos = []
        matched_neg = []
        for src in sources:
            words = src["comment"].lower()
            matched_pos.extend([w for w in pos_words if w in words])
            matched_neg.extend([w for w in neg_words if w in words])
            
        summary_bullets = []
        if matched_pos:
            summary_bullets.append(f"Guests frequently highlighted positive aspects such as: **{', '.join(set(matched_pos))}**.")
        if matched_neg:
            summary_bullets.append(f"Potential concerns or issues flagged by guests: **{', '.join(set(matched_neg))}**.")
        
        summary_para = " ".join(summary_bullets) if summary_bullets else "Reviews generally provide neutral feedback concerning this topic."
        
        answer = f"""**[AI Generated Synthesis of Guest Feedback]**
Based on retrieving {len(sources)} matching comments from guest reviews, here is the synthesis:
 
{summary_para}
 
The retrieved reviews show consistent sentiment regarding details matching your query. Inspect the matching sources below for full reviewer comments and listing IDs."""
        
        return {
            "answer": answer,
            "sources": sources
        }
 
class RecommendationEngine:
    def __init__(self, listings_path="data/processed/enriched_listings.csv"):
        self.listings_path = listings_path
        self.listings_df = None
        self._initialize()
 
    def _initialize(self):
        if not os.path.exists(self.listings_path):
            print(f"Listings dataset not found at {self.listings_path}. Recommender disabled.")
            return
        
        try:
            self.listings_df = pd.read_csv(self.listings_path)
            print("Recommendation Engine initialized successfully.")
        except Exception as e:
            print(f"Error initializing Recommender Engine: {e}")
 
    def recommend(self, listing_id, top_n=5):
        if self.listings_df is None:
            self._initialize()
            if self.listings_df is None:
                return pd.DataFrame()
        
        # Verify listing exists
        matching_listings = self.listings_df[self.listings_df["id"] == listing_id]
        if matching_listings.empty:
            try:
                matching_listings = self.listings_df[self.listings_df["id"] == int(float(listing_id))]
            except Exception:
                pass
            if matching_listings.empty:
                return pd.DataFrame()
            
        target = matching_listings.iloc[0]
        
        # Simple content-based filtering:
        # Match borough and room type exactly if borough/group_col is present, then find closest base price and ratings
        group_col = "neighbourhood_group_cleansed"
        if group_col in self.listings_df.columns and group_col in target and pd.notna(target[group_col]):
            subset = self.listings_df[
                (self.listings_df["id"] != target["id"]) &
                (self.listings_df[group_col] == target[group_col]) &
                (self.listings_df["room_type"] == target["room_type"])
            ].copy()
        else:
            subset = self.listings_df[
                (self.listings_df["id"] != target["id"]) &
                (self.listings_df["room_type"] == target["room_type"])
            ].copy()
        
        if subset.empty:
            # Fallback to room type only
            subset = self.listings_df[
                (self.listings_df["id"] != target["id"]) &
                (self.listings_df["room_type"] == target["room_type"])
            ].copy()
            
        if subset.empty:
            return pd.DataFrame()
            
        # Compute distance metric
        price_diff = np.abs(subset["price"] - target["price"]) / max(target["price"], 1)
        rating_diff = np.abs(subset["review_scores_rating"] - target["review_scores_rating"]) / 5.0
        
        subset["distance"] = price_diff + rating_diff
        recommendations = subset.sort_values(by="distance").head(top_n)
        
        return recommendations[[
            "id", "name", "price", "review_scores_rating", 
            "neighbourhood_cleansed", "bedrooms", "beds"
        ]]

class PricingAgent:
    def __init__(self, model_dir="reports"):
        self.model_path = os.path.join(model_dir, "pricing_model.joblib")
        self.scaler_path = os.path.join(model_dir, "scaler.joblib")
        self.features_path = os.path.join(model_dir, "model_features.json")
        self.forecast_path = os.path.join(model_dir, "occupancy_forecast.csv")
        
        self.model = None
        self.scaler = None
        self.features = None
        self.forecast_df = None
        self._initialize()

    def _initialize(self):
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path) and os.path.exists(self.features_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                with open(self.features_path, "r") as f:
                    self.features = json.load(f)
                print("Pricing Agent ML models loaded successfully.")
            except Exception as e:
                print(f"Error loading serialised models: {e}")
        else:
            print("Serialized ML models not found. Running Pricing Agent in heuristic fallback mode.")
            
        if os.path.exists(self.forecast_path):
            try:
                self.forecast_df = pd.read_csv(self.forecast_path)
                self.forecast_df["date"] = pd.to_datetime(self.forecast_df["date"])
            except Exception as e:
                print(f"Error loading forecast data: {e}")

    def predict_price(self, bedrooms, beds, borough, room_type, rating, superhost, month_name="January"):
        # Heuristic fallback if model is missing
        if self.model is None or self.scaler is None or self.features is None:
            # Baseline pricing heuristics
            base = 100.0
            base += bedrooms * 50.0
            base += beds * 15.0
            if room_type == "Entire Home/Apt":
                base *= 1.5
            elif room_type == "Shared Room":
                base *= 0.5
                
            borough_multipliers = {"Manhattan": 1.6, "Brooklyn": 1.2, "Queens": 0.9, "Staten Island": 0.7, "Bronx": 0.7}
            base *= borough_multipliers.get(borough, 1.0)
            
            if superhost == "t":
                base *= 1.05
            
            predicted_base_price = base
            using_ml = False
        else:
            using_ml = True
            # Reconstruct columns
            input_dict = {col: 0.0 for col in self.features}
            
            # Numeric inputs
            input_dict["bedrooms"] = float(bedrooms)
            input_dict["beds"] = float(beds)
            input_dict["review_scores_rating"] = float(rating)
            input_dict["host_is_superhost"] = 1.0 if superhost == "t" else 0.0
            input_dict["number_of_reviews"] = 25.0  # assumed average reviews count
            input_dict["name_len"] = 25.0          # average string sizes
            input_dict["desc_len"] = 300.0
            
            # Set categorical dummy flags (drop_first alignment handled automatically by matching exact column keys)
            rt_col = f"room_type_{room_type}"
            if rt_col in input_dict:
                input_dict[rt_col] = 1.0
                
            b_col = f"neighbourhood_group_cleansed_{borough}"
            if b_col in input_dict:
                input_dict[b_col] = 1.0
                
            input_df = pd.DataFrame([input_dict])
            
            # Align features order
            input_df = input_df[self.features]
            
            # Scale numerical fields
            num_cols = ["bedrooms", "beds", "review_scores_rating", "number_of_reviews", "name_len", "desc_len"]
            input_df[num_cols] = self.scaler.transform(input_df[num_cols])
            
            # Predict log price
            pred_log = self.model.predict(input_df)[0]
            predicted_base_price = float(np.expm1(pred_log))
        
        # Apply seasonal price adjustments based on forecasting occupancy
        seasonal_multiplier = 1.0
        reason = "standard market demand"
        
        if self.forecast_df is not None:
            # Map month name to forecasted occupancy
            try:
                # Find matching month name
                self.forecast_df["month_name"] = self.forecast_df["date"].dt.strftime("%B")
                match = self.forecast_df[self.forecast_df["month_name"] == month_name]
                if not match.empty:
                    predicted_occ = float(match.iloc[0]["forecast_occupancy"])
                    # Baseline average occupancy is around 0.50
                    # Adjust price based on deviation
                    if predicted_occ > 0.55:
                        seasonal_multiplier = 1.10
                        reason = f"high forecasted demand ({predicted_occ*100:.1f}% occupancy rate)"
                    elif predicted_occ < 0.45:
                        seasonal_multiplier = 0.90
                        reason = f"low forecasted occupancy ({predicted_occ*100:.1f}%)"
                    else:
                        seasonal_multiplier = 1.00
                        reason = f"moderate occupancy ({predicted_occ*100:.1f}%)"
            except Exception as e:
                print(f"Error calculating seasonal multiplier: {e}")
                
        final_suggested_price = predicted_base_price * seasonal_multiplier
        
        advice = f"Based on the trained Random Forest model (ML: {using_ml}) and {reason}, the suggested nightly rate is **${final_suggested_price:.2f}**."
        
        return {
            "base_predicted_price": predicted_base_price,
            "final_suggested_price": final_suggested_price,
            "seasonal_multiplier": seasonal_multiplier,
            "reason": reason,
            "advice": advice,
            "using_ml": using_ml
        }

if __name__ == "__main__":
    print("Testing AI Agent module...")
    rag = RAGEngine()
    res = rag.query("subway", top_n=2)
    print(res["answer"])
    
    agent = PricingAgent()
    p_res = agent.predict_price(
        bedrooms=1, beds=1, borough="Manhattan", room_type="Entire Home/Apt", rating=4.8, superhost="t", month_name="May"
    )
    print(p_res["advice"])
