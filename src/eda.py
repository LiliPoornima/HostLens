import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set visual style
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16
})

# Custom palette based on Expernetic/Airbnb theme
PRIMARY_COLOR = "#003366"  # Dark Blue
SECONDARY_COLOR = "#FF5A5F"  # Coral
ACCENT_COLOR = "#484848"  # Dark Grey
PALETTE = [PRIMARY_COLOR, SECONDARY_COLOR, "#00A699", "#FC642D", "#767676"]

def generate_eda_visualizations():
    print("Starting EDA visualizations...")
    os.makedirs("reports/figures", exist_ok=True)
    
    # Load enriched data
    df = pd.read_csv("data/processed/enriched_listings.csv")
    calendar = pd.read_csv("data/raw/calendar.csv")
    calendar["date"] = pd.to_datetime(calendar["date"])
    
    # Merge listings price with calendar to get daily prices
    listings_price = df[["id", "price", "neighbourhood_group_cleansed"]].rename(columns={"id": "listing_id"})
    calendar_merged = calendar.merge(listings_price, on="listing_id", how="inner")
    
    # 1. Price Distribution (Log-Price to manage skew)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df["price"], bins=100, kde=True, color=PRIMARY_COLOR, ax=ax)
    ax.set_xlim(0, 1000)
    ax.set_title("Distribution of Listing Prices (Capped at $1000)")
    ax.set_xlabel("Price ($)")
    ax.set_ylabel("Count")
    plt.tight_layout()
    plt.savefig("reports/figures/01_price_distribution.png", dpi=300)
    plt.close()
    
    # Log-price distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(np.log1p(df["price"]), bins=50, kde=True, color=SECONDARY_COLOR, ax=ax)
    ax.set_title("Log-Transformed Price Distribution")
    ax.set_xlabel("Log(Price + 1)")
    ax.set_ylabel("Density")
    plt.tight_layout()
    plt.savefig("reports/figures/01_log_price_distribution.png", dpi=300)
    plt.close()

    # 2. Price by Borough & Room Type
    fig, ax = plt.subplots(figsize=(10, 6))
    order = df.groupby("neighbourhood_group_cleansed")["price"].median().sort_values(ascending=False).index
    sns.boxplot(
        data=df, 
        x="neighbourhood_group_cleansed", 
        y="price", 
        hue="room_type", 
        order=order,
        palette=PALETTE,
        showfliers=False,
        ax=ax
    )
    ax.set_title("Listing Prices by Borough and Room Type (Outliers Hidden)")
    ax.set_xlabel("Borough")
    ax.set_ylabel("Price per Night ($)")
    plt.legend(title="Room Type", loc="upper right")
    plt.tight_layout()
    plt.savefig("reports/figures/02_price_by_borough_roomtype.png", dpi=300)
    plt.close()

    # 3. Host Portfolios (Single vs Commercial operators)
    # Classify hosts by portfolio size
    portfolio = df.groupby("host_id").size().reset_index(name="listings_count")
    bins = [0, 1, 2, 5, 10, 10000]
    labels = ["Single Listing (1)", "Duplex (2)", "Small Portfolio (3-5)", "Medium Portfolio (6-10)", "Commercial Operator (11+)"]
    portfolio["portfolio_segment"] = pd.cut(portfolio["listings_count"], bins=bins, labels=labels)
    segment_counts = portfolio["portfolio_segment"].value_counts(normalize=True).sort_index() * 100
    
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=segment_counts.values, y=segment_counts.index, palette="Blues_r", ax=ax)
    ax.set_title("Host Segments by Portfolio Size (% of Total Hosts)")
    ax.set_xlabel("Percentage (%)")
    ax.set_ylabel("Portfolio Segment")
    for i, v in enumerate(segment_counts.values):
        ax.text(v + 1, i, f"{v:.1f}%", va='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig("reports/figures/03_host_portfolio_distribution.png", dpi=300)
    plt.close()

    # 4. Review Rating Distributions (Rating Inflation)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df["review_scores_rating"], bins=30, kde=True, color="#00A699", ax=ax)
    ax.set_title("Distribution of Review Ratings (Highlighting Left Skew)")
    ax.set_xlabel("Review Score Rating (0 - 5)")
    ax.set_ylabel("Count")
    plt.tight_layout()
    plt.savefig("reports/figures/04_rating_distribution.png", dpi=300)
    plt.close()

    # 5. Spatial Pricing Gradients
    fig, ax = plt.subplots(figsize=(10, 8))
    # Filter listings with price < 500 for better contrast
    spatial_df = df[df["price"] <= 500]
    scatter = ax.scatter(
        spatial_df["longitude"], 
        spatial_df["latitude"], 
        c=spatial_df["price"], 
        cmap="viridis", 
        s=2, 
        alpha=0.6
    )
    fig.colorbar(scatter, label="Price ($)", ax=ax)
    ax.set_title("Geographic Pricing Gradients in New York City (Prices <= $500)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    plt.savefig("reports/figures/05_spatial_price_map.png", dpi=300)
    plt.close()

    # 6. Seasonality Analysis
    # Occupancy rate and average price monthly
    calendar_merged["month"] = calendar_merged["date"].dt.to_period("M")
    calendar_merged["is_booked"] = calendar_merged["available"].map({"f": 1, "t": 0})
    
    monthly_data = calendar_merged.groupby("month").agg(
        occupancy_rate=("is_booked", "mean"),
        avg_price=("price", "mean")
    ).reset_index()
    monthly_data["month_str"] = monthly_data["month"].astype(str)
    
    # Plot occupancy and price seasonality
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    color = SECONDARY_COLOR
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Occupancy Rate", color=color)
    line1 = ax1.plot(monthly_data["month_str"], monthly_data["occupancy_rate"] * 100, color=color, marker='o', label="Occupancy Rate (%)")
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xticklabels(monthly_data["month_str"], rotation=45)
    
    ax2 = ax1.twinx()  
    color = PRIMARY_COLOR
    ax2.set_ylabel("Average Base Price ($)", color=color)
    line2 = ax2.plot(monthly_data["month_str"], monthly_data["avg_price"], color=color, marker='x', linestyle='--', label="Average Price ($)")
    ax2.tick_params(axis='y', labelcolor=color)
    
    # added these lines
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    plt.title("Seasonality: Occupancy Rate vs Average Listing Price in NYC")
    plt.tight_layout()
    plt.savefig("reports/figures/06_seasonality_analysis.png", dpi=300)
    plt.close()

    print("EDA visualizations generated successfully.")

if __name__ == "__main__":
    generate_eda_visualizations()
