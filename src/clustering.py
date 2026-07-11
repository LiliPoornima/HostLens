import os
import json
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

def run_clustering(city="nyc"):
    print(f"Starting Listing & Host Segmentation for {city.upper()}...")
    os.makedirs("reports", exist_ok=True)
    
    # Load dataset
    df = pd.read_csv(f"data/processed/enriched_listings_{city}.csv")
    
    # ─────────────────────────────────────────────
    # 1. LISTING SEGMENTATION
    # ─────────────────────────────────────────────
    print("Pre-processing listing data for clustering...")
    cluster_cols = [
        "id", "price", "review_scores_rating", "latitude", "longitude", 
        "availability_365", "calculated_host_listings_count", "neighbourhood_group_cleansed"
    ]
    # Drop rows missing crucial coordinates or price
    list_df = df[cluster_cols].dropna(subset=["price", "latitude", "longitude"]).copy()
    
    # Impute missing ratings with median
    list_df["review_scores_rating"] = list_df["review_scores_rating"].fillna(list_df["review_scores_rating"].median())
    
    # Select feature columns to scale
    feat_cols = ["price", "review_scores_rating", "latitude", "longitude", "availability_365", "calculated_host_listings_count"]
    
    scaler = StandardScaler()
    scaled_feats = scaler.fit_transform(list_df[feat_cols])
    
    # Fit K-Means
    k_listings = 4
    print(f"Fitting K-Means on listings with K={k_listings}...")
    kmeans_list = KMeans(n_clusters=k_listings, random_state=42, n_init=10)
    list_df["cluster_id"] = kmeans_list.fit_predict(scaled_feats)
    
    # Compute Silhouette Score
    sample_size = min(5000, len(list_df))
    if sample_size > 0:
        sample_df = list_df.sample(n=sample_size, random_state=42)
        sample_scaled = scaler.transform(sample_df[feat_cols])
        sil_score_list = float(silhouette_score(sample_scaled, sample_df["cluster_id"]))
    else:
        sil_score_list = 0.0
    print(f"Listing Silhouette Score (N={sample_size}): {sil_score_list:.4f}")
    
    # Profile Listing Clusters
    list_profiles = []
    for cid in range(k_listings):
        grp = list_df[list_df["cluster_id"] == cid]
        avg_price = float(grp["price"].mean()) if not grp.empty else 0.0
        avg_rating = float(grp["review_scores_rating"].mean()) if not grp.empty else 0.0
        avg_avail = float(grp["availability_365"].mean()) if not grp.empty else 0.0
        avg_host_count = float(grp["calculated_host_listings_count"].mean()) if not grp.empty else 0.0
        top_borough = str(grp["neighbourhood_group_cleansed"].mode().iloc[0] if not grp["neighbourhood_group_cleansed"].empty else "Unknown")
        count = int(len(grp))
        
        # Heuristically assign profile label
        if count == 0:
            label = "Standard Urban Hubs"
        elif avg_price > df["price"].quantile(0.85):
            label = "Premium Listings"
        elif avg_host_count > 10.0:
            label = "Corporate Multi-Listings"
        elif avg_price < df["price"].quantile(0.40):
            label = "Budget Outer-Borough"
        else:
            label = "Standard Urban Hubs"
            
        list_profiles.append({
            "cluster_id": cid,
            "profile_label": label,
            "size": count,
            "avg_price": round(avg_price, 2),
            "avg_rating": round(avg_rating, 2),
            "avg_availability": round(avg_avail, 1),
            "avg_host_listings_count": round(avg_host_count, 1),
            "primary_borough": top_borough
        })
        
    print("Listing cluster profiles computed.")
    
    # Merge cluster ID back to main enriched listings and save
    df = df.drop(columns=["listing_cluster"], errors="ignore")
    df = df.merge(list_df[["id", "cluster_id"]].rename(columns={"cluster_id": "listing_cluster"}), on="id", how="left")
    df["listing_cluster"] = df["listing_cluster"].fillna(-1).astype(int)
    
    df.to_csv(f"data/processed/enriched_listings_{city}.csv", index=False)
    if city == "nyc":
        df.to_csv("data/processed/enriched_listings.csv", index=False)
    print(f"Saved listing cluster assignments to data/processed/enriched_listings_{city}.csv")
    
    # ─────────────────────────────────────────────
    # 2. HOST SEGMENTATION
    # ─────────────────────────────────────────────
    print("Preparing host metrics for segmentation...")
    # Aggregate by host_id
    host_df = df.groupby("host_id").agg(
        listings_count=("id", "count"),
        avg_price=("price", "mean"),
        avg_rating=("review_scores_rating", "mean"),
        superhost_ratio=("host_is_superhost", lambda x: (x == "t").mean())
    ).reset_index().dropna()
    
    host_feats = ["listings_count", "avg_price", "avg_rating", "superhost_ratio"]
    scaler_host = StandardScaler()
    scaled_hosts = scaler_host.fit_transform(host_df[host_feats])
    
    k_hosts = 3
    print(f"Fitting K-Means on hosts with K={k_hosts}...")
    kmeans_host = KMeans(n_clusters=k_hosts, random_state=42, n_init=10)
    host_df["cluster_id"] = kmeans_host.fit_predict(scaled_hosts)
    
    # Compute Host Silhouette Score
    host_sample = min(5000, len(host_df))
    if host_sample > 0:
        host_sample_df = host_df.sample(n=host_sample, random_state=42)
        host_sample_scaled = scaler_host.transform(host_sample_df[host_feats])
        sil_score_host = float(silhouette_score(host_sample_scaled, host_sample_df["cluster_id"]))
    else:
        sil_score_host = 0.0
    print(f"Host Silhouette Score (N={host_sample}): {sil_score_host:.4f}")
    
    # Profile Host Clusters
    host_profiles = []
    for cid in range(k_hosts):
        grp = host_df[host_df["cluster_id"] == cid]
        avg_list_count = float(grp["listings_count"].mean()) if not grp.empty else 0.0
        avg_p = float(grp["avg_price"].mean()) if not grp.empty else 0.0
        avg_r = float(grp["avg_rating"].mean()) if not grp.empty else 0.0
        avg_sh = float(grp["superhost_ratio"].mean()) if not grp.empty else 0.0
        count = int(len(grp))
        
        # Label hosts
        if count == 0:
            label = "Casual Hosts"
        elif avg_list_count > 5.0:
            label = "Commercial Operators"
        elif avg_sh > 0.5:
            label = "High-Quality Superhosts"
        else:
            label = "Casual Hosts"
            
        host_profiles.append({
            "cluster_id": cid,
            "profile_label": label,
            "size": count,
            "avg_listings_count": round(avg_list_count, 1),
            "avg_price": round(avg_p, 2),
            "avg_rating": round(avg_r, 2),
            "superhost_ratio": round(avg_sh, 2)
        })
        
    print("Host cluster profiles computed.")
    
    # ─────────────────────────────────────────────
    # 3. SAVE RESULTS
    # ─────────────────────────────────────────────
    output_metrics = {
        "listings": {
            "silhouette_score": sil_score_list,
            "profiles": list_profiles
        },
        "hosts": {
            "silhouette_score": sil_score_host,
            "profiles": host_profiles
        }
    }
    
    with open(f"reports/clustering_metrics_{city}.json", "w") as f:
        json.dump(output_metrics, f, indent=4)
    if city == "nyc":
        with open("reports/clustering_metrics.json", "w") as f:
            json.dump(output_metrics, f, indent=4)
    print(f"Saved clustering metrics and profiles to reports/clustering_metrics_{city}.json")
    
    # Save a CSV with host assignments for mapping/plotting in dashboard
    host_df.to_csv(f"reports/host_clustering_assignments_{city}.csv", index=False)
    if city == "nyc":
        host_df.to_csv("reports/host_clustering_assignments.csv", index=False)
    print(f"Saved host cluster assignments to reports/host_clustering_assignments_{city}.csv")
    print(f"Clustering complete for {city.upper()}!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run clustering for a specific city.")
    parser.add_argument("--city", type=str, default="nyc", choices=["nyc", "boston", "sf"])
    args = parser.parse_args()
    run_clustering(args.city)
