import streamlit as st
import pandas as pd
import numpy as np
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="HostLens · Airbnb Market Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "HostLens — Built for the Expernec Data Engineering Assessment"}
)

# ─────────────────────────────────────────────
# GLOBAL CSS — DARK GLASSMORPHISM THEME
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0d1117; color: #e6edf3; }
  .stApp { background: linear-gradient(135deg, #0d1117 0%, #161b22 60%, #0d1117 100%); }

  section[data-testid="stSidebar"] {
      background: linear-gradient(180deg, #161b22 0%, #0d1117 100%) !important;
      border-right: 1px solid rgba(255,255,255,0.07);
  }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stSlider label,
  section[data-testid="stSidebar"] p { color: #8b949e !important; font-size: 12px; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; }

  .stTabs [data-baseweb="tab-list"] { background: rgba(22,27,34,0.7); border-radius: 12px; padding: 4px; border: 1px solid rgba(255,255,255,0.06); backdrop-filter: blur(10px); }
  .stTabs [data-baseweb="tab"] { color: #8b949e !important; font-weight: 500; font-size: 13px; border-radius: 8px; padding: 8px 18px; transition: all 0.2s ease; }
  .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #FF5A5F, #FC642D) !important; color: white !important; box-shadow: 0 4px 15px rgba(255,90,95,0.35); }

  .glass-card { background: rgba(22,27,34,0.6); border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; padding: 24px; backdrop-filter: blur(12px); transition: all 0.3s ease; margin-bottom: 16px; }
  .glass-card:hover { border-color: rgba(255,90,95,0.3); box-shadow: 0 8px 32px rgba(255,90,95,0.1); transform: translateY(-2px); }

  .kpi-card { background: rgba(22,27,34,0.8); border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; padding: 20px 24px; text-align: center; position: relative; overflow: hidden; transition: transform 0.2s ease, box-shadow 0.2s ease; }
  .kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 16px 16px 0 0; }
  .kpi-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }
  .kpi-card.red::before   { background: linear-gradient(90deg, #FF5A5F, #FC642D); }
  .kpi-card.teal::before  { background: linear-gradient(90deg, #00A699, #00ccbb); }
  .kpi-card.blue::before  { background: linear-gradient(90deg, #3a86ff, #5e9eff); }
  .kpi-card.gold::before  { background: linear-gradient(90deg, #f7b731, #f0c22d); }
  .kpi-card.purple::before { background: linear-gradient(90deg, #a855f7, #7c3aed); }
  .kpi-icon { font-size: 28px; margin-bottom: 8px; }
  .kpi-value { font-size: 28px; font-weight: 800; color: #e6edf3; line-height: 1.1; letter-spacing: -0.5px; }
  .kpi-label { font-size: 11px; color: #6e7681; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 6px; font-weight: 600; }
  .kpi-delta { font-size: 12px; margin-top: 4px; font-weight: 500; }
  .kpi-delta.up { color: #3fb950; }

  .section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.07); }
  .section-header h3 { margin: 0; font-size: 17px; font-weight: 700; color: #e6edf3; }
  .section-pill { background: rgba(255,90,95,0.15); color: #FF5A5F; border: 1px solid rgba(255,90,95,0.3); border-radius: 20px; padding: 2px 10px; font-size: 11px; font-weight: 600; }

  .hero-banner { background: linear-gradient(135deg, rgba(255,90,95,0.12) 0%, rgba(0,166,153,0.08) 50%, rgba(58,134,255,0.1) 100%); border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; padding: 32px 36px; margin-bottom: 28px; position: relative; overflow: hidden; }
  .hero-banner::after { content: '🏙️'; position: absolute; right: 36px; top: 50%; transform: translateY(-50%); font-size: 72px; opacity: 0.15; }
  .hero-title { font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #FF5A5F, #FC642D, #f7b731); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0; }
  .hero-subtitle { color: #8b949e; font-size: 15px; margin-top: 6px; }
  .hero-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); border-radius: 20px; padding: 4px 12px; font-size: 12px; font-weight: 600; margin-top: 12px; }

  .stTextArea textarea { background: #0d1117 !important; color: #58a6ff !important; border: 1px solid rgba(88,166,255,0.2) !important; border-radius: 8px !important; font-family: 'JetBrains Mono', 'Fira Code', monospace !important; font-size: 13px !important; }
  .stButton > button { background: linear-gradient(135deg, #FF5A5F, #FC642D) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; padding: 8px 24px !important; transition: all 0.2s ease !important; }
  .stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(255,90,95,0.4) !important; }

  .stSelectbox > div > div { background: rgba(22,27,34,0.8) !important; border-color: rgba(255,255,255,0.1) !important; }
  div[data-testid="stMetricValue"] { color: #e6edf3 !important; font-weight: 700 !important; }
  div[data-testid="stMetricLabel"] p { color: #6e7681 !important; }
  .stDataFrame { border-radius: 12px; overflow: hidden; }
  thead tr th { background: #161b22 !important; color: #8b949e !important; }
  hr { border-color: rgba(255,255,255,0.06) !important; }
  .stAlert { border-radius: 10px !important; }

  .sidebar-brand { text-align: center; padding: 20px 0 24px; border-bottom: 1px solid rgba(255,255,255,0.07); margin-bottom: 20px; }
  .sidebar-brand-title { font-size: 22px; font-weight: 800; background: linear-gradient(135deg, #FF5A5F, #FC642D); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .sidebar-brand-sub { font-size: 11px; color: #6e7681; letter-spacing: 0.1em; text-transform: uppercase; }
  .filter-label { font-size: 11px; color: #6e7681; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv("data/processed/enriched_listings.csv")
    return df

@st.cache_data(ttl=300)
def load_report(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

@st.cache_data(ttl=300)
def load_metadata():
    path = "reports/pipeline_metadata.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

try:
    df = load_data()
except Exception as e:
    st.error(f"**Data Load Error** — Run the ETL pipeline first: `python src/pipeline.py`\n\n{e}")
    st.stop()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div style="font-size:36px;margin-bottom:4px">🏠</div>
        <div class="sidebar-brand-title">HostLens</div>
        <div class="sidebar-brand-sub">Market Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="filter-label">📍 Borough</p>', unsafe_allow_html=True)
    boroughs = ["All"] + sorted(df["neighbourhood_group_cleansed"].dropna().unique().tolist())
    selected_borough = st.selectbox("Borough", boroughs, label_visibility="collapsed")

    st.markdown('<p class="filter-label">🛏️ Room Type</p>', unsafe_allow_html=True)
    room_types = ["All"] + sorted(df["room_type"].dropna().unique().tolist())
    selected_room_type = st.selectbox("Room Type", room_types, label_visibility="collapsed")

    st.markdown('<p class="filter-label">💰 Price Range ($/night)</p>', unsafe_allow_html=True)
    price_min, price_max = int(df["price"].min()), int(df["price"].quantile(0.98))
    price_range = st.slider("Price", price_min, price_max, (price_min, min(500, price_max)), label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<p class="filter-label">ℹ️ Dataset</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="color:#6e7681;font-size:12px;line-height:1.7">
    🗄️ <b style="color:#8b949e">{len(df):,}</b> total listings<br>
    📅 NYC Airbnb snapshot<br>
    🔗 Source: Inside Airbnb
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")
    if st.button("🔄 Refresh Data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
filtered_df = df.copy()
if selected_borough != "All":
    filtered_df = filtered_df[filtered_df["neighbourhood_group_cleansed"] == selected_borough]
if selected_room_type != "All":
    filtered_df = filtered_df[filtered_df["room_type"] == selected_room_type]
filtered_df = filtered_df[
    (filtered_df["price"] >= price_range[0]) &
    (filtered_df["price"] <= price_range[1])
]

# ─────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hero-banner">
    <p class="hero-title">HostLens · NYC Airbnb Intelligence</p>
    <p class="hero-subtitle">End-to-end data engineering, analytics, and ML insights for the New York City short-term rental market.</p>
    <div class="hero-badge">🟢 Live · {len(filtered_df):,} listings matching filters</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Market Overview",
    "🗺️ Map Explorer",
    "👥 Host & Reviews",
    "🤖 ML & Explainability",
    "🔮 Occupancy Forecast",
    "⚙️ Pipeline Telemetry",
    "💻 SQL Console",
    "🤖 AI Intelligence Hub"
])

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(22,27,34,0.5)",
    font=dict(family="Inter", color="#8b949e"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.07)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.07)"),
    margin=dict(t=30, b=40, l=40, r=20),
)

BRAND_COLORS = ["#FF5A5F", "#00A699", "#FC642D", "#3a86ff", "#f7b731", "#a855f7", "#3fb950"]

# ════════════════════════════════════════════
# TAB 1 — MARKET OVERVIEW
# ════════════════════════════════════════════
with tab1:
    avg_price = filtered_df["price"].mean()
    avg_rating = filtered_df["review_scores_rating"].mean()
    avg_occ = filtered_df["occupancy_rate"].mean() * 100 if "occupancy_rate" in filtered_df.columns else 0
    avg_rev = filtered_df["estimated_annual_revenue"].mean() if "estimated_annual_revenue" in filtered_df.columns else 0
    total_hosts = filtered_df["host_id"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    kpi_config = [
        (c1, "red",    "🏘️", f"{len(filtered_df):,}",  "Active Listings",   "📍 In selection"),
        (c2, "teal",   "💰", f"${avg_price:.0f}",       "Avg Nightly Price", f"Median ${filtered_df['price'].median():.0f}"),
        (c3, "gold",   "⭐", f"{avg_rating:.2f}",       "Avg Rating",        "Out of 5.00"),
        (c4, "blue",   "📅", f"{avg_occ:.1f}%",         "Avg Occupancy",     "Calendar estimate"),
        (c5, "purple", "👤", f"{total_hosts:,}",        "Unique Hosts",      "Host diversity"),
    ]
    for col, color, icon, val, lbl, delta in kpi_config:
        with col:
            st.markdown(f"""
            <div class="kpi-card {color}">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-label">{lbl}</div>
                <div class="kpi-delta up">{delta}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.markdown('<div class="section-header"><h3>Price Distribution by Borough</h3><span class="section-pill">Interactive</span></div>', unsafe_allow_html=True)
        borough_order = (
            filtered_df.groupby("neighbourhood_group_cleansed")["price"]
            .median().sort_values(ascending=False).index.tolist()
        )
        fig_box = px.box(
            filtered_df[filtered_df["price"] <= filtered_df["price"].quantile(0.95)],
            x="neighbourhood_group_cleansed", y="price",
            color="neighbourhood_group_cleansed",
            category_orders={"neighbourhood_group_cleansed": borough_order},
            color_discrete_sequence=BRAND_COLORS,
            labels={"neighbourhood_group_cleansed": "Borough", "price": "Price ($/night)"},
        )
        fig_box.update_layout(**PLOTLY_THEME, showlegend=False)
        fig_box.update_traces(marker=dict(opacity=0.7))
        st.plotly_chart(fig_box, width="stretch")

    with r1c2:
        st.markdown('<div class="section-header"><h3>Room Type Share</h3><span class="section-pill">Distribution</span></div>', unsafe_allow_html=True)
        room_counts = filtered_df["room_type"].value_counts().reset_index()
        room_counts.columns = ["room_type", "count"]
        fig_donut = px.pie(
            room_counts, values="count", names="room_type",
            color_discrete_sequence=BRAND_COLORS, hole=0.55,
        )
        fig_donut.update_traces(textposition="outside", textinfo="percent+label",
                                marker=dict(line=dict(color="#0d1117", width=3)))
        fig_donut.update_layout(**PLOTLY_THEME, showlegend=True,
                                legend=dict(orientation="h", y=-0.15, font=dict(size=11)))
        st.plotly_chart(fig_donut, width="stretch")

    r2c1, r2c2 = st.columns(2)

    with r2c1:
        st.markdown('<div class="section-header"><h3>Average Price by Borough & Room Type</h3></div>', unsafe_allow_html=True)
        grp = filtered_df.groupby(["neighbourhood_group_cleansed", "room_type"])["price"].mean().reset_index()
        fig_bar = px.bar(
            grp, x="neighbourhood_group_cleansed", y="price",
            color="room_type", barmode="group",
            color_discrete_sequence=BRAND_COLORS,
            labels={"neighbourhood_group_cleansed": "Borough", "price": "Avg Price ($)", "room_type": "Room Type"},
        )
        fig_bar.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig_bar, width="stretch")

    with r2c2:
        st.markdown('<div class="section-header"><h3>Price vs Rating Scatter</h3></div>', unsafe_allow_html=True)
        scatter_df = filtered_df[["price", "review_scores_rating", "neighbourhood_group_cleansed"]].dropna()
        scatter_df = scatter_df[scatter_df["price"] <= 600]
        fig_sc = px.scatter(
            scatter_df.sample(min(3000, len(scatter_df)), random_state=42),
            x="price", y="review_scores_rating",
            color="neighbourhood_group_cleansed",
            color_discrete_sequence=BRAND_COLORS,
            opacity=0.55,
            labels={"price": "Price ($/night)", "review_scores_rating": "Review Score",
                    "neighbourhood_group_cleansed": "Borough"},
            trendline="lowess",
        )
        fig_sc.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig_sc, width="stretch")

# ════════════════════════════════════════════
# TAB 2 — MAP EXPLORER
# ════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header"><h3>Geographic Price Heatmap — New York City</h3><span class="section-pill">Hover for Details</span></div>', unsafe_allow_html=True)

    map_df = (
        filtered_df[["latitude", "longitude", "price", "room_type",
                      "neighbourhood_group_cleansed", "neighbourhood_cleansed"]]
        .dropna().query("price <= 800")
    )
    map_df = map_df.sample(min(8000, len(map_df)), random_state=1)

    fig_map = px.scatter_mapbox(
        map_df, lat="latitude", lon="longitude",
        color="price", size="price", size_max=12,
        color_continuous_scale=["#00A699", "#f7b731", "#FF5A5F"],
        range_color=[map_df["price"].quantile(0.05), map_df["price"].quantile(0.95)],
        hover_name="neighbourhood_cleansed",
        hover_data={"latitude": False, "longitude": False, "price": True,
                    "room_type": True, "neighbourhood_group_cleansed": True},
        mapbox_style="carto-darkmatter",
        zoom=10, center={"lat": 40.7128, "lon": -74.0060}, opacity=0.8,
        labels={"price": "Price ($/night)", "neighbourhood_group_cleansed": "Borough", "room_type": "Room Type"},
    )
    fig_map.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=0, l=0, r=0),
        height=560,
        coloraxis_colorbar=dict(
            title=dict(text="Price<br>($/night)", font=dict(color="#8b949e")),
            thicknessmode="pixels", thickness=14,
            lenmode="fraction", len=0.6,
            bgcolor="rgba(22,27,34,0.8)",
            bordercolor="rgba(255,255,255,0.07)",
            tickfont=dict(color="#8b949e"),
        ),
    )
    st.plotly_chart(fig_map, width="stretch")

    st.markdown('<div class="section-header"><h3>Listing Density by Borough</h3></div>', unsafe_allow_html=True)
    dens = filtered_df["neighbourhood_group_cleansed"].value_counts().reset_index()
    dens.columns = ["Borough", "Listings"]
    dens["Share (%)"] = (dens["Listings"] / dens["Listings"].sum() * 100).round(1)
    fig_dens = px.bar(
        dens, x="Listings", y="Borough", orientation="h",
        color="Listings", color_continuous_scale=["#003366", "#FF5A5F"],
        text="Share (%)",
    )
    fig_dens.update_traces(texttemplate="%{text}%", textposition="outside")
    dens_layout = {**PLOTLY_THEME, "showlegend": False, "coloraxis_showscale": False, "height": 280}
    dens_layout["yaxis"] = {**PLOTLY_THEME["yaxis"], "categoryorder": "total ascending"}
    fig_dens.update_layout(**dens_layout)
    st.plotly_chart(fig_dens, width="stretch")

# ════════════════════════════════════════════
# TAB 3 — HOST & REVIEWS
# ════════════════════════════════════════════
with tab3:
    r1, r2 = st.columns(2)

    with r1:
        st.markdown('<div class="section-header"><h3>Host Portfolio Segments</h3><span class="section-pill">Commercial vs Personal</span></div>', unsafe_allow_html=True)
        portfolio = filtered_df.groupby("host_id").size().reset_index(name="count")
        bins   = [0, 1, 2, 5, 10, 50, 10000]
        labels = ["Solo (1)", "Pair (2)", "Small (3-5)", "Mid (6-10)", "Large (11-50)", "Commercial (50+)"]
        portfolio["Segment"] = pd.cut(portfolio["count"], bins=bins, labels=labels)
        seg_counts = portfolio["Segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Hosts"]
        seg_counts = seg_counts.sort_values("Hosts", ascending=True)
        fig_port = px.bar(
            seg_counts, x="Hosts", y="Segment", orientation="h",
            color="Hosts", color_continuous_scale=["#003366", "#00A699"], text="Hosts",
        )
        fig_port.update_traces(textposition="outside")
        fig_port.update_layout(**PLOTLY_THEME, coloraxis_showscale=False, height=320)
        st.plotly_chart(fig_port, width="stretch")

    with r2:
        st.markdown('<div class="section-header"><h3>Review Score Distribution</h3></div>', unsafe_allow_html=True)
        rating_df = filtered_df["review_scores_rating"].dropna()
        fig_hist = px.histogram(rating_df, nbins=40, color_discrete_sequence=["#FF5A5F"],
                                labels={"value": "Review Score", "count": "Listings"})
        fig_hist.update_layout(**PLOTLY_THEME, bargap=0.08, xaxis_title="Review Score", yaxis_title="Listings")
        st.plotly_chart(fig_hist, width="stretch")

    # Superhost comparison
    st.markdown('<div class="section-header"><h3>Superhost vs Regular Host — Key Metrics</h3></div>', unsafe_allow_html=True)
    if "host_is_superhost" in filtered_df.columns:
        sh_df = filtered_df.copy()
        sh_df["Host Type"] = sh_df["host_is_superhost"].map(
            lambda x: "⭐ Superhost" if str(x).strip().lower() in ["t", "true", "1"] else "Regular Host"
        )
        metrics_to_compare = ["price", "review_scores_rating", "reviews_per_month"]
        metric_labels = {"price": "Avg Price ($/night)", "review_scores_rating": "Avg Rating", "reviews_per_month": "Reviews/Month"}
        super_grp = sh_df.groupby("Host Type")[metrics_to_compare].mean().reset_index()
        fig_super = make_subplots(rows=1, cols=3,
                                   subplot_titles=[metric_labels[m] for m in metrics_to_compare])
        colors_sh = {"⭐ Superhost": "#f7b731", "Regular Host": "#8b949e"}
        for i, metric in enumerate(metrics_to_compare, 1):
            for _, row in super_grp.iterrows():
                fig_super.add_trace(go.Bar(
                    name=row["Host Type"], x=[row["Host Type"]], y=[row[metric]],
                    marker_color=colors_sh[row["Host Type"]], showlegend=(i == 1),
                ), row=1, col=i)
        fig_super.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(22,27,34,0.5)",
            font=dict(family="Inter", color="#8b949e"),
            height=320, barmode="group",
            legend=dict(orientation="h", y=1.15, font=dict(size=11)),
            margin=dict(t=50, b=30, l=30, r=20),
        )
        for ax in fig_super.layout:
            if ax.startswith("xaxis") or ax.startswith("yaxis"):
                fig_super.layout[ax].update(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.07)")
        st.plotly_chart(fig_super, width="stretch")

    # Sentiment scatter
    st.markdown('<div class="section-header"><h3>Sentiment Score vs Review Rating</h3></div>', unsafe_allow_html=True)
    if "avg_review_sentiment" in filtered_df.columns:
        sent_df = filtered_df[filtered_df["avg_review_sentiment"] != 0][
            ["avg_review_sentiment", "review_scores_rating", "neighbourhood_group_cleansed"]
        ].dropna()
        if not sent_df.empty:
            fig_sent = px.scatter(
                sent_df.sample(min(3000, len(sent_df)), random_state=42),
                x="avg_review_sentiment", y="review_scores_rating",
                color="neighbourhood_group_cleansed",
                color_discrete_sequence=BRAND_COLORS, opacity=0.6, trendline="ols",
                labels={"avg_review_sentiment": "Lexicon Sentiment Score",
                        "review_scores_rating": "Platform Rating",
                        "neighbourhood_group_cleansed": "Borough"},
            )
            fig_sent.update_layout(**PLOTLY_THEME)
            st.plotly_chart(fig_sent, width="stretch")
        else:
            st.info("No sentiment data points available for the current filter.")
    else:
        st.info("ℹ️ Sentiment scores not computed yet. Run `python src/machine_learning.py`.")

# ════════════════════════════════════════════
# TAB 4 — ML & EXPLAINABILITY
# ════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div class="glass-card">
        <div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:28px">🤖</div>
            <div>
                <div style="font-size:16px;font-weight:700;color:#e6edf3">Pricing Model Explainability</div>
                <div style="font-size:13px;color:#8b949e">Random Forest · Gradient Boosting · Permutation Importance · Bias Detection</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    mc1, mc2 = st.columns(2)

    with mc1:
        st.markdown('<div class="section-header"><h3>Permutation Feature Importance</h3><span class="section-pill">Top 10</span></div>', unsafe_allow_html=True)
        df_perm = load_report("reports/permutation_importance.csv")
        if df_perm is not None:
            top10 = df_perm.head(10).sort_values("importance")
            fig_imp = px.bar(
                top10, x="importance", y="feature", orientation="h",
                color="importance", color_continuous_scale=["#003366", "#FF5A5F"],
                labels={"importance": "Importance Decrease (MAE)", "feature": "Feature"}, text="importance",
            )
            fig_imp.update_traces(texttemplate="%{text:.3f}", textposition="outside")
            fig_imp.update_layout(**PLOTLY_THEME, coloraxis_showscale=False, height=380)
            st.plotly_chart(fig_imp, width="stretch")
        else:
            st.warning("⚠️ Run `python src/machine_learning.py` to generate importance metrics.")

    with mc2:
        st.markdown('<div class="section-header"><h3>LDA Review Topic Keywords</h3><span class="section-pill">5 Themes</span></div>', unsafe_allow_html=True)
        df_topics = load_report("reports/nlp_review_topics.csv")
        if df_topics is not None:
            topic_colors = {0: "#FF5A5F", 1: "#00A699", 2: "#f7b731", 3: "#3a86ff", 4: "#a855f7"}
            for idx, row in df_topics.iterrows():
                tid = int(row["topic_id"]) if "topic_id" in row else idx
                color = topic_colors.get(tid % 5, "#8b949e")
                theme = row.get("theme", f"Topic {tid}")
                keywords = row.get("top_keywords", "")
                st.markdown(f"""
                <div class="glass-card" style="border-left:3px solid {color};padding:14px 18px;margin-bottom:10px">
                    <div style="font-size:12px;color:{color};font-weight:700;text-transform:uppercase;letter-spacing:0.07em">Topic {tid} · {theme}</div>
                    <div style="font-size:13px;color:#8b949e;margin-top:4px">{keywords}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Run `python src/machine_learning.py` to generate LDA topics.")

    st.markdown("---")
    st.markdown('<div class="section-header"><h3>Model Bias Analysis — Prediction Errors by Segment</h3><span class="section-pill">MAE & MAPE</span></div>', unsafe_allow_html=True)

    bc1, bc2 = st.columns(2)
    with bc1:
        df_bias_b = load_report("reports/model_bias_borough.csv")
        if df_bias_b is not None:
            fig_bb = px.bar(
                df_bias_b.sort_values("mape", ascending=False),
                x="borough", y="mape", color="mape",
                color_continuous_scale=["#3fb950", "#f7b731", "#f85149"],
                text="mape", labels={"borough": "Borough", "mape": "MAPE (%)"},
            )
            fig_bb.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_bb.update_layout(**PLOTLY_THEME, coloraxis_showscale=False,
                                  title="MAPE by Borough", title_font=dict(color="#e6edf3", size=14))
            st.plotly_chart(fig_bb, width="stretch")
            st.dataframe(df_bias_b.style.background_gradient(subset=["mape"], cmap="Reds"), width="stretch")

    with bc2:
        df_bias_r = load_report("reports/model_bias_room_type.csv")
        if df_bias_r is not None:
            fig_br = px.bar(
                df_bias_r.sort_values("mape", ascending=False),
                x="room_type", y="mape", color="mape",
                color_continuous_scale=["#3fb950", "#f7b731", "#f85149"],
                text="mape", labels={"room_type": "Room Type", "mape": "MAPE (%)"},
            )
            fig_br.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_br.update_layout(**PLOTLY_THEME, coloraxis_showscale=False,
                                  title="MAPE by Room Type", title_font=dict(color="#e6edf3", size=14))
            st.plotly_chart(fig_br, width="stretch")
            st.dataframe(df_bias_r.style.background_gradient(subset=["mape"], cmap="Reds"), width="stretch")

# ════════════════════════════════════════════
# TAB 5 — OCCUPANCY FORECAST
# ════════════════════════════════════════════
with tab5:
    st.markdown("""
    <div class="glass-card">
        <div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:28px">🔮</div>
            <div>
                <div style="font-size:16px;font-weight:700;color:#e6edf3">Occupancy Rate Forecasting</div>
                <div style="font-size:13px;color:#8b949e">Holt's Linear Exponential Smoothing · 6-Month Projection · Aggregated Calendar Data</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_forecast = load_report("reports/occupancy_forecast.csv")
    if df_forecast is not None:
        df_forecast["date"] = pd.to_datetime(df_forecast["date"])
        df_forecast["occ_pct"] = df_forecast["forecast_occupancy"] * 100

        n_hist = max(len(df_forecast) - 6, 1)
        df_hist_part = df_forecast.iloc[:n_hist]
        df_fore_part = df_forecast.iloc[n_hist-1:]

        fig_fore = go.Figure()
        fig_fore.add_trace(go.Scatter(
            x=df_hist_part["date"], y=df_hist_part["occ_pct"],
            mode="lines+markers", name="Historical Occupancy",
            line=dict(color="#00A699", width=2.5), marker=dict(size=5),
        ))
        fig_fore.add_trace(go.Scatter(
            x=df_fore_part["date"], y=df_fore_part["occ_pct"],
            mode="lines+markers", name="Forecasted Occupancy",
            line=dict(color="#FF5A5F", width=2.5, dash="dot"),
            marker=dict(size=6, symbol="diamond"),
        ))
        fig_fore.add_vrect(
            x0=df_fore_part["date"].iloc[0], x1=df_fore_part["date"].iloc[-1],
            fillcolor="rgba(255,90,95,0.06)", line_width=0,
            annotation_text="Forecast Zone",
            annotation_font=dict(color="#FF5A5F", size=11),
            annotation_position="top left",
        )
        fig_fore.update_layout(
            **PLOTLY_THEME, height=380,
            xaxis_title="Month", yaxis_title="Occupancy Rate (%)",
            legend=dict(orientation="h", y=1.1, font=dict(size=11)),
            hovermode="x unified",
        )
        st.plotly_chart(fig_fore, width="stretch")

        st.markdown('<div class="section-header"><h3>Monthly Forecast Table</h3></div>', unsafe_allow_html=True)
        fc1, fc2 = st.columns([2, 1])
        with fc1:
            display = df_forecast[["date", "occ_pct"]].copy()
            display.columns = ["Month", "Forecasted Occupancy (%)"]
            display["Month"] = display["Month"].dt.strftime("%B %Y")
            display["Forecasted Occupancy (%)"] = display["Forecasted Occupancy (%)"].round(2)
            st.dataframe(
                display.style.background_gradient(subset=["Forecasted Occupancy (%)"], cmap="RdYlGn"),
                width="stretch"
            )
        with fc2:
            peak   = display.loc[display["Forecasted Occupancy (%)"].idxmax()]
            trough = display.loc[display["Forecasted Occupancy (%)"].idxmin()]
            st.markdown(f"""
            <div class="glass-card">
                <div class="kpi-label">📈 Peak Month</div>
                <div style="font-size:18px;font-weight:700;color:#3fb950;margin-top:6px">{peak['Month']}</div>
                <div style="font-size:14px;color:#8b949e">{peak['Forecasted Occupancy (%)']:.1f}%</div>
            </div>
            <div class="glass-card">
                <div class="kpi-label">📉 Trough Month</div>
                <div style="font-size:18px;font-weight:700;color:#f85149;margin-top:6px">{trough['Month']}</div>
                <div style="font-size:14px;color:#8b949e">{trough['Forecasted Occupancy (%)']:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Forecast artifacts not found. Run `python src/forecasting.py` to generate.")

# ════════════════════════════════════════════
# TAB 6 — PIPELINE TELEMETRY
# ════════════════════════════════════════════
with tab6:
    st.markdown("""
    <div class="glass-card">
        <div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:28px">⚙️</div>
            <div>
                <div style="font-size:16px;font-weight:700;color:#e6edf3">Pipeline Telemetry & Audit Log</div>
                <div style="font-size:13px;color:#8b949e">Runtime metrics, data counts, and ingestion profiling from the automated ETL pipeline</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    metadata = load_metadata()
    if metadata:
        status_color = "#3fb950" if metadata.get("status") == "SUCCESS" else "#f85149"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:20px">
            <div style="width:8px;height:8px;background:{status_color};border-radius:50%;box-shadow:0 0 8px {status_color}"></div>
            <span style="color:{status_color};font-weight:600;font-size:13px">{metadata.get('status','UNKNOWN')}</span>
            <span style="color:#6e7681;font-size:13px">· Run ID: {metadata.get('run_id','—')}</span>
            <span style="color:#6e7681;font-size:13px">· {metadata.get('run_timestamp','—')}</span>
        </div>
        """, unsafe_allow_html=True)

        t1, t2, t3, t4 = st.columns(4)
        telemetry_cards = [
            (t1, "🗂️", f"{metadata.get('listings_raw_count', 0):,}",   "Raw Listings"),
            (t2, "📆", f"{metadata.get('calendar_raw_count', 0):,}",   "Raw Calendar Rows"),
            (t3, "💬", f"{metadata.get('reviews_raw_count', 0):,}",    "Raw Review Rows"),
            (t4, "✅", f"{metadata.get('listings_cleaned_count', 0):,}", "Cleaned Listings"),
        ]
        for col, icon, val, lbl in telemetry_cards:
            with col:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center">
                    <div style="font-size:24px">{icon}</div>
                    <div style="font-size:22px;font-weight:800;color:#e6edf3;margin-top:4px">{val}</div>
                    <div style="font-size:11px;color:#6e7681;text-transform:uppercase;letter-spacing:0.06em;margin-top:4px">{lbl}</div>
                </div>
                """, unsafe_allow_html=True)

        st.write("")
        d1, d2 = st.columns(2)
        with d1:
            dup_count   = metadata.get("duplicate_listings_count", 0)
            fuzzy_count = metadata.get("fuzzy_matches_count", 0)
            st.markdown(f"""
            <div class="glass-card">
                <div class="kpi-label">🔍 Data Quality Checks</div>
                <div style="margin-top:12px;display:flex;gap:20px">
                    <div>
                        <div style="font-size:20px;font-weight:700;color:#f85149">{dup_count:,}</div>
                        <div style="font-size:11px;color:#6e7681">Exact Duplicates Removed</div>
                    </div>
                    <div>
                        <div style="font-size:20px;font-weight:700;color:#f7b731">{fuzzy_count:,}</div>
                        <div style="font-size:11px;color:#6e7681">Fuzzy Matches Found</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with d2:
            clean_rate = (metadata.get('listings_cleaned_count', 0) / max(metadata.get('listings_raw_count', 1), 1) * 100)
            st.markdown(f"""
            <div class="glass-card">
                <div class="kpi-label">📊 Pipeline Health</div>
                <div style="margin-top:12px">
                    <div style="font-size:26px;font-weight:800;color:#3fb950">{clean_rate:.1f}%</div>
                    <div style="font-size:12px;color:#6e7681;margin-top:4px">Data Retention Rate after Cleaning</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Pipeline metadata not found. Run `python src/pipeline.py` first.")

    st.markdown("---")
    st.markdown('<div class="section-header"><h3>Data Profiling Summary</h3></div>', unsafe_allow_html=True)
    df_profiling = load_report("reports/data_profiling_summary.csv")
    if df_profiling is not None:
        num_cols = df_profiling.select_dtypes("number").columns.tolist()
        st.dataframe(
            df_profiling.style.background_gradient(subset=num_cols, cmap="Blues"),
            width="stretch"
        )
    else:
        st.info("No profiling data available.")

# ════════════════════════════════════════════
# TAB 7 — SQL CONSOLE
# ════════════════════════════════════════════
with tab7:
    st.markdown("""
    <div class="glass-card">
        <div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:28px">💻</div>
            <div>
                <div style="font-size:16px;font-weight:700;color:#e6edf3">Interactive SQL Console</div>
                <div style="font-size:13px;color:#8b949e">Query the DuckDB star schema directly — real-time results rendered below</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sc1, sc2 = st.columns([2, 1])

    with sc2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size:12px;font-weight:700;color:#8b949e;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:12px">📋 Schema Reference</div>
        """, unsafe_allow_html=True)
        schema_tables = {
            "fact_listings":      ["listing_id", "host_id", "neighbourhood_cleansed", "price", "number_of_reviews", "review_scores_rating"],
            "dim_hosts":          ["host_id", "host_name", "host_is_superhost", "host_location"],
            "dim_property":       ["listing_id", "property_type", "room_type", "bedrooms", "beds"],
            "dim_neighbourhoods": ["neighbourhood_cleansed", "neighbourhood_group_cleansed"],
            "dim_reviews":        ["listing_id", "first_review", "last_review"],
            "metadata_log":       ["run_id", "run_timestamp", "listings_raw_count", "status"],
        }
        for table, cols in schema_tables.items():
            st.markdown(f"""
            <div style="margin-bottom:10px">
                <code style="color:#58a6ff;font-size:12px">{table}</code>
                <div style="font-size:11px;color:#6e7681;margin-top:3px">{', '.join(cols)}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="kpi-label" style="margin-bottom:8px">⚡ Quick Queries</div>', unsafe_allow_html=True)
        presets = {
            "Top 10 highest priced listings":  "SELECT listing_id, price FROM fact_listings ORDER BY price DESC LIMIT 10;",
            "Average price by borough":        "SELECT neighbourhood_cleansed, AVG(price) as avg_price FROM fact_listings GROUP BY 1 ORDER BY avg_price DESC LIMIT 20;",
            "Superhost count":                 "SELECT host_is_superhost, COUNT(*) FROM dim_hosts GROUP BY 1;",
            "Recent pipeline run":             "SELECT * FROM metadata_log ORDER BY run_timestamp DESC LIMIT 1;",
        }
        selected_preset = st.selectbox("Load preset", ["(none)"] + list(presets.keys()), label_visibility="collapsed")

    with sc1:
        default_query = presets.get(selected_preset, "SELECT * FROM fact_listings LIMIT 10;") if selected_preset != "(none)" else "SELECT * FROM fact_listings LIMIT 10;"
        user_query = st.text_area("SQL Query", value=default_query, height=160,
                                   label_visibility="collapsed", placeholder="Write your SQL query here…")
        col_btn1, col_btn2, _ = st.columns([1, 1, 3])
        with col_btn1:
            run_clicked = st.button("▶ Run Query", width="stretch")
        with col_btn2:
            if st.button("🗑 Clear", width="stretch"):
                st.rerun()

        if run_clicked:
            try:
                conn = duckdb.connect("data/processed/hostlens.db")
                result_df = conn.execute(user_query).fetchdf()
                conn.close()
                st.success(f"✅ Query returned **{len(result_df):,} rows** · {len(result_df.columns)} columns")
                st.dataframe(
                    result_df.style.highlight_max(axis=0, color="rgba(255,90,95,0.15)"),
                    width="stretch"
                )
                csv_data = result_df.to_csv(index=False).encode()
                st.download_button("⬇ Export CSV", csv_data, "query_result.csv", "text/csv")
            except Exception as e:
                st.error(f"**SQL Error:** {e}")

# ════════════════════════════════════════════
# TAB 8 — AI INTELLIGENCE HUB
# ════════════════════════════════════════════
@st.cache_resource
def get_rag_engine():
    from ai_agent import RAGEngine
    return RAGEngine()

@st.cache_resource
def get_recommender():
    from ai_agent import RecommendationEngine
    return RecommendationEngine()

@st.cache_resource
def get_pricing_agent():
    from ai_agent import PricingAgent
    return PricingAgent()

with tab8:
    st.markdown("""
    <div class="glass-card">
        <div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:28px">🤖</div>
            <div>
                <div style="font-size:16px;font-weight:700;color:#e6edf3">HostLens AI Intelligence Hub</div>
                <div style="font-size:13px;color:#8b949e">Retrieval-Augmented Generation (RAG) Q&A Console, Content-Based recommendations, and ML-Powered Dynamic Pricing Agent</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sub-tabs
    ai_sub1, ai_sub2, ai_sub3 = st.tabs([
        "🔍 Reviews Q&A Console (RAG)",
        "🏠 Listing Recommender",
        "💡 Dynamic Pricing Advisor"
    ])
    
    with ai_sub1:
        st.markdown('<div class="section-header"><h3>Semantic Search & Q&A over Guest Reviews</h3><span class="section-pill">RAG Engine</span></div>', unsafe_allow_html=True)
        st.markdown("Query the guest reviews database semantically. The RAG engine retrieves matching reviews using TF-IDF and synthesizes reviewer feedback.")
        user_query = st.text_input("Ask a question about listings or reviews:", value="Is the subway close or noisy?")
        if st.button("Query Reviews", width="stretch"):
            with st.spinner("Retrieving and synthesizing review comments..."):
                rag_engine = get_rag_engine()
                res = rag_engine.query(user_query)
                st.markdown(res["answer"])
                
                if res["sources"]:
                    st.write("")
                    st.markdown("#### Retrieved Source Comments:")
                    for idx, src in enumerate(res["sources"], 1):
                        st.markdown(f"""
                        <div class="glass-card" style="padding:14px; margin-bottom:10px;">
                            <div style="font-size:11px; color:#FF5A5F; font-weight:600;">Source {idx} · Score: {src['similarity']:.2f} · Date: {src['date']} · Listing: {src['listing_id']}</div>
                            <div style="font-size:13px; color:#8b949e; margin-top:4px;">"{src['comment']}"</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
    with ai_sub2:
        st.markdown('<div class="section-header"><h3>Content-Based Listing Recommendation System</h3><span class="section-pill">Recommendation Engine</span></div>', unsafe_allow_html=True)
        st.markdown("Choose an active listing ID to find the top 5 most similar listing alternatives in the same neighbourhood.")
        listing_options = sorted(df["id"].dropna().unique().tolist())
        selected_listing_id = st.selectbox("Select Target Listing ID:", listing_options[:200]) # limit dropdown size
        if st.button("Generate Recommendations", width="stretch"):
            recommender = get_recommender()
            recs = recommender.recommend(selected_listing_id)
            if not recs.empty:
                st.success("Matching listing recommendations found:")
                st.dataframe(recs, width="stretch")
            else:
                st.warning("No similar listings found. Try selecting another listing ID.")
                
    with ai_sub3:
        st.markdown('<div class="section-header"><h3>AI-Driven Seasonal Dynamic Pricing Agent</h3><span class="section-pill">ML Pricing Agent</span></div>', unsafe_allow_html=True)
        st.markdown("Input listing configuration and get a fair baseline nightly price predicted by the Random Forest model, adjusted dynamically based on monthly occupancy forecasting peaks and troughs.")
        
        pr_c1, pr_c2 = st.columns(2)
        with pr_c1:
            in_borough = st.selectbox("Borough:", sorted(df["neighbourhood_group_cleansed"].dropna().unique().tolist()))
            in_room_type = st.selectbox("Room Type:", sorted(df["room_type"].dropna().unique().tolist()))
            in_month = st.selectbox("Month of Year:", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
        with pr_c2:
            in_bedrooms = st.slider("Bedrooms count:", 0, 5, 1)
            in_beds = st.slider("Beds count:", 1, 10, 1)
            in_rating = st.slider("Target reviews score rating:", 1.0, 5.0, 4.8, 0.1)
            in_superhost = st.checkbox("Superhost badge status", value=True)
            superhost_str = "t" if in_superhost else "f"
            
        if st.button("Calculate Suggested Rate", width="stretch"):
            agent = get_pricing_agent()
            p_res = agent.predict_price(
                bedrooms=in_bedrooms,
                beds=in_beds,
                borough=in_borough,
                room_type=in_room_type,
                rating=in_rating,
                superhost=superhost_str,
                month_name=in_month
            )
            
            st.write("")
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; border-left:4px solid #FF5A5F;">
                <div class="kpi-label">💡 Suggested Nightly Rate</div>
                <div style="font-size:36px; font-weight:800; color:#e6edf3; margin-top:8px;">${p_res['final_suggested_price']:.2f}</div>
                <div style="font-size:13px; color:#8b949e; margin-top:8px;">Base Predicted Price: ${p_res['base_predicted_price']:.2f}</div>
                <div style="font-size:13px; color:#8b949e; margin-top:4px;">Seasonal Adjustment: x{p_res['seasonal_multiplier']:.2f} ({p_res['reason']})</div>
                <div style="font-size:12px; color:#3fb950; font-weight:600; margin-top:12px;">{p_res['advice']}</div>
            </div>
            """, unsafe_allow_html=True)

