import streamlit as st
import pandas as pd
import numpy as np
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns

# Set page config
st.set_page_config(
    page_title="HostLens - Airbnb Market Intelligence Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .reportview-container {
        background-color: #f5f7f9;
    }
    .main-title {
        color: #003366;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        margin-bottom: 20px;
    }
    .kpi-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 4px solid #FF5A5F;
    }
    .kpi-val {
        font-size: 32px;
        font-weight: bold;
        color: #003366;
    }
    .kpi-lbl {
        font-size: 14px;
        color: #767676;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Load data helper
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/enriched_listings.csv")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading datasets. Please make sure the ETL pipeline has run. Details: {e}")
    st.stop()

# Sidebar Filters
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/6/69/Airbnb_Logo_B%C3%A9lo.svg", width=120)
st.sidebar.title("Filters")
boroughs = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique().tolist())
selected_borough = st.sidebar.selectbox("Select Borough", boroughs)

room_types = ["All"] + sorted(df["room_type"].dropna().unique().tolist())
selected_room_type = st.sidebar.selectbox("Select Room Type", room_types)

# Filter dataframe
filtered_df = df.copy()
if selected_borough != "All":
    filtered_df = filtered_df[filtered_df["neighbourhood_group_cleansed"] == selected_borough]
if selected_room_type != "All":
    filtered_df = filtered_df[filtered_df["room_type"] == selected_room_type]

# Header
st.markdown("<h1 class='main-title'>🏠 HostLens: Airbnb Market Intelligence</h1>", unsafe_allow_html=True)
st.markdown("An end-to-end data engineering and analytics dashboard for the New York City Airbnb marketplace.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Market Overview", "🗺️ Map Explorer", "👥 Host & Review Insights", "💻 SQL Console"])

# Tab 1: Market Overview
with tab1:
    # Key Performance Indicators
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"<div class='kpi-box'><div class='kpi-val'>{len(filtered_df):,}</div><div class='kpi-lbl'>Active Listings</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='kpi-box'><div class='kpi-val'>${filtered_df['price'].mean():.2f}</div><div class='kpi-lbl'>Average Price</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='kpi-box'><div class='kpi-val'>{filtered_df['review_scores_rating'].mean():.2f} ★</div><div class='kpi-lbl'>Average Rating</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='kpi-box'><div class='kpi-val'>{filtered_df['occupancy_rate'].mean() * 100:.1f}%</div><div class='kpi-lbl'>Occupancy Rate</div></div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='kpi-box'><div class='kpi-val'>${filtered_df['estimated_annual_revenue'].mean():,.2f}</div><div class='kpi-lbl'>Average Est. Revenue</div></div>", unsafe_allow_html=True)
        
    st.write("")
    
    # Visualizations
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Price Distribution by Borough")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.boxplot(
            data=filtered_df,
            x="neighbourhood_group_cleansed",
            y="price",
            palette="Set2",
            showfliers=False,
            ax=ax
        )
        ax.set_xlabel("Borough")
        ax.set_ylabel("Price ($)")
        plt.xticks(rotation=45)
        st.pyplot(fig)
        
    with col_chart2:
        st.subheader("Room Type Distribution")
        fig, ax = plt.subplots(figsize=(8, 4))
        room_counts = filtered_df["room_type"].value_counts()
        ax.pie(room_counts, labels=room_counts.index, autopct="%1.1f%%", startangle=90, colors=["#003366", "#FF5A5F", "#00A699", "#FC642D"])
        st.pyplot(fig)

# Tab 2: Map Explorer
with tab2:
    st.subheader("Geographic Distribution of Listings")
    st.markdown("Filter and hover over the map to explore pricing gradients. Point color/size represents listing locations.")
    
    # Prepare map data
    map_df = filtered_df[["latitude", "longitude", "price"]].dropna().copy()
    # Crop price for map display aesthetics
    map_df = map_df[map_df["price"] <= 1000]
    
    # Streamlit map
    st.map(map_df, latitude="latitude", longitude="longitude")

# Tab 3: Host & Review Insights
with tab3:
    col_h1, col_h2 = st.columns(2)
    
    with col_h1:
        st.subheader("Host Portfolio Breakdown")
        portfolio = filtered_df.groupby("host_id").size().reset_index(name="listings_count")
        bins = [0, 1, 2, 5, 10, 10000]
        labels = ["Single Listing (1)", "Duplex (2)", "Small Portfolio (3-5)", "Medium Portfolio (6-10)", "Commercial (11+)"]
        portfolio["portfolio_segment"] = pd.cut(portfolio["listings_count"], bins=bins, labels=labels)
        segment_counts = portfolio["portfolio_segment"].value_counts(normalize=True).sort_index() * 100
        
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(x=segment_counts.values, y=segment_counts.index, palette="Blues_r", ax=ax)
        ax.set_xlabel("Percentage (%)")
        ax.set_ylabel("Host Segment")
        st.pyplot(fig)
        
    with col_h2:
        st.subheader("Sentiment Analysis vs Review Rating Correlation")
        if "avg_review_sentiment" not in filtered_df.columns:
            st.info(
                "⚠️ Sentiment scores not yet computed. "
                "Run `python src/machine_learning.py` to generate them, "
                "then restart the dashboard."
            )
        else:
            st.markdown(
                "Scatter plot of average listing sentiment score "
                "(from lexicon NLP analysis) vs the platform rating."
            )
            fig, ax = plt.subplots(figsize=(8, 4))
            sentiment_plot_df = filtered_df[
                filtered_df["avg_review_sentiment"] != 0
            ][["avg_review_sentiment", "review_scores_rating"]].dropna()
            if sentiment_plot_df.empty:
                ax.text(0.5, 0.5, "No sentiment data available",
                        ha="center", va="center", transform=ax.transAxes)
            else:
                sns.scatterplot(
                    data=sentiment_plot_df,
                    x="avg_review_sentiment",
                    y="review_scores_rating",
                    color="#00A699",
                    alpha=0.6,
                    ax=ax
                )
            ax.set_xlabel("Average Sentiment Score (-10 to 10)")
            ax.set_ylabel("Review Rating Score")
            st.pyplot(fig)

# Tab 4: SQL Console
with tab4:
    st.subheader("Execute SQL Queries against DuckDB")
    st.markdown("""
    Explore the database schema:
    - `dim_hosts` (host_id, host_name, host_is_superhost, host_location)
    - `dim_neighbourhoods` (neighbourhood_cleansed, neighbourhood_group_cleansed)
    - `dim_property` (listing_id, property_type, room_type, bedrooms, beds)
    - `dim_reviews` (listing_id, first_review, last_review)
    - `fact_listings` (listing_id, host_id, neighbourhood_cleansed, price, number_of_reviews, review_scores_rating, reviews_per_month, total_reviews)
    """)
    
    # Query text area
    default_query = "SELECT * FROM fact_listings LIMIT 5;"
    user_query = st.text_area("Write SQL Query", value=default_query, height=120)
    
    if st.button("Run Query"):
        try:
            conn = duckdb.connect("data/processed/hostlens.db")
            res_df = conn.execute(user_query).fetchdf()
            st.success("Query executed successfully!")
            st.dataframe(res_df)
            conn.close()
        except Exception as e:
            st.error(f"SQL Error: {e}")
