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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Market Overview", 
    "🗺️ Map Explorer", 
    "👥 Host & Review Insights", 
    "🤖 Advanced ML & Explainability",
    "🔮 Occupancy Forecast",
    "📋 Pipeline Logs & Telemetry",
    "💻 SQL Console"
])

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

# Tab 4: Advanced ML & Explainability
with tab4:
    st.subheader("🤖 Pricing Model Explainability & Operational Bias Analysis")
    st.markdown("This tab displays advanced machine learning results including robust permutation importance and model performance bias checks.")
    
    col_ml1, col_ml2 = st.columns(2)
    
    with col_ml1:
        st.subheader("Permutation Feature Importance")
        st.markdown("Unlike raw Gini importances, Permutation Importance measures how much the validation score drops when a feature is shuffled.")
        try:
            df_perm = pd.read_csv("reports/permutation_importance.csv")
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=df_perm.head(10), x="importance", y="feature", palette="viridis", ax=ax)
            ax.set_xlabel("Mean Importances Decrease")
            ax.set_ylabel("Feature")
            st.pyplot(fig)
        except Exception:
            st.warning("⚠️ Permutation importance CSV not found. Run `python src/machine_learning.py` to compile.")

    with col_ml2:
        st.subheader("Review Topics Extracted via LDA")
        st.markdown("We run Latent Dirichlet Allocation (LDA) on reviews comments to classify feedback categories automatically.")
        try:
            df_topics = pd.read_csv("reports/nlp_review_topics.csv")
            st.table(df_topics)
        except Exception:
            st.warning("⚠️ Review topics CSV not found. Run `python src/machine_learning.py` to compile.")

    st.markdown("---")
    st.subheader("🔍 Model Generalizability & Geographic Bias Analysis")
    st.markdown("Evaluating pricing errors (MAE and MAPE) across boroughs and operational room types to identify model biases.")
    
    col_bias1, col_bias2 = st.columns(2)
    with col_bias1:
        st.write("#### Performance by Borough")
        try:
            df_bias_b = pd.read_csv("reports/model_bias_borough.csv")
            st.dataframe(df_bias_b)
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(data=df_bias_b, x="borough", y="mape", palette="coolwarm", ax=ax)
            ax.set_ylabel("Mean Absolute Percentage Error (%)")
            ax.set_xlabel("Borough")
            st.pyplot(fig)
        except Exception:
            st.warning("⚠️ Borough bias metrics not found.")
            
    with col_bias2:
        st.write("#### Performance by Room Type")
        try:
            df_bias_r = pd.read_csv("reports/model_bias_room_type.csv")
            st.dataframe(df_bias_r)
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(data=df_bias_r, x="room_type", y="mape", palette="coolwarm", ax=ax)
            ax.set_ylabel("Mean Absolute Percentage Error (%)")
            ax.set_xlabel("Room Type")
            plt.xticks(rotation=15)
            st.pyplot(fig)
        except Exception:
            st.warning("⚠️ Room type bias metrics not found.")

# Tab 5: Occupancy Forecast
with tab5:
    st.subheader("🔮 NYC Occupancy Rate Forecasting (Next 6 Months)")
    st.markdown("Utilizing historical daily calendar booking data aggregated monthly to predict future NYC occupancy rates using Holt's Linear Exponential Smoothing.")
    
    try:
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            st.image("reports/figures/07_occupancy_forecast.png", use_container_width=True)
        with col_f2:
            st.markdown("#### Forecast Summary")
            df_f = pd.read_csv("reports/occupancy_forecast.csv")
            df_f["forecast_occupancy"] = (df_f["forecast_occupancy"] * 100).round(2).astype(str) + "%"
            st.table(df_f)
    except Exception as e:
        st.warning(f"⚠️ Forecast artifacts not found. Run `python src/forecasting.py` to compile. Details: {e}")

# Tab 6: Pipeline Logs & Telemetry
with tab6:
    st.subheader("📋 Pipeline Logs & Telemetry")
    st.markdown("Real-time telemetry and validation summaries from the automated data pipeline.")
    
    try:
        with open("reports/pipeline_metadata.json", "r") as f:
            metadata = json = pd.read_json("reports/pipeline_metadata.json", typ="series")
        
        st.write("#### Pipeline Telemetry Summary")
        col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
        col_meta1.metric("Run ID", metadata["run_id"])
        col_meta2.metric("Run Timestamp", metadata["run_timestamp"])
        col_meta3.metric("Cleaned Listings Count", f"{metadata['listings_cleaned_count']:,}")
        col_meta4.metric("ETL Status", metadata["status"])
        
        st.markdown("---")
        st.write("#### Raw Ingested Row Counts")
        col_raw1, col_raw2, col_raw3 = st.columns(3)
        col_raw1.metric("Raw Listings Rows", f"{metadata['listings_raw_count']:,}")
        col_raw2.metric("Raw Calendar Rows", f"{metadata['calendar_raw_count']:,}")
        col_raw3.metric("Raw Reviews Rows", f"{metadata['reviews_raw_count']:,}")
        
    except Exception:
        st.warning("⚠️ Pipeline metadata JSON not found. Run `python src/pipeline.py` first.")
        
    st.markdown("---")
    st.write("#### Ingestion Profiling Summary")
    try:
        df_profiling = pd.read_csv("reports/data_profiling_summary.csv")
        st.dataframe(df_profiling)
    except Exception:
        st.warning("⚠️ Data profiling CSV not found.")

# Tab 7: SQL Console
with tab7:
    st.subheader("Execute SQL Queries against DuckDB")
    st.markdown("""
    Explore the database schema:
    - `dim_hosts` (host_id, host_name, host_is_superhost, host_location)
    - `dim_neighbourhoods` (neighbourhood_cleansed, neighbourhood_group_cleansed)
    - `dim_property` (listing_id, property_type, room_type, bedrooms, beds)
    - `dim_reviews` (listing_id, first_review, last_review)
    - `fact_listings` (listing_id, host_id, neighbourhood_cleansed, price, number_of_reviews, review_scores_rating, reviews_per_month, total_reviews)
    - `metadata_log` (run_id, run_timestamp, listings_raw_count, calendar_raw_count, reviews_raw_count, listings_cleaned_count, duplicate_listings_count, fuzzy_matches_count, status)
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
