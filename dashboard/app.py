import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BTC/USDT Trading Dashboard",
    page_icon="",
    layout="wide"
)

# ── Translations ──────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "EN": {
        "title": "BTC/USDT Trading Dashboard",
        "subtitle": "Data updated hourly via Airflow pipeline",
        "current_price": "Current Price",
        "sma7": "SMA 7",
        "sma20": "SMA 20",
        "volume": "Volume",
        "chart_title": "BTC/USDT — Candlestick + Moving Averages",
        "chart2_title": "Hourly Price Change (%)",
        "time": "Time",
        "price": "Price (USDT)",
        "change": "Change (%)",
        "raw_data": "Raw data",
        "no_data": "No data available. Run the Airflow pipeline first.",
        "built_by": "Built by",
        "pipeline": "Airflow pipeline",
        "theme": "Theme",
        "lang": "Language",
    },
    "DE": {
        "title": "BTC/USDT Handels-Dashboard",
        "subtitle": "Daten werden stundlich uber die Airflow-Pipeline aktualisiert",
        "current_price": "Aktueller Preis",
        "sma7": "GDL 7",
        "sma20": "GDL 20",
        "volume": "Volumen",
        "chart_title": "BTC/USDT — Kerzenchart + Gleitende Durchschnitte",
        "chart2_title": "Stundliche Preisanderung (%)",
        "time": "Zeit",
        "price": "Preis (USDT)",
        "change": "Anderung (%)",
        "raw_data": "Rohdaten",
        "no_data": "Keine Daten verfugbar. Bitte zuerst die Airflow-Pipeline ausfuhren.",
        "built_by": "Erstellt von",
        "pipeline": "Airflow-Pipeline",
        "theme": "Design",
        "lang": "Sprache",
    }
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
def apply_theme(dark: bool):
    if dark:
        bg = "#0f1117"
        card_bg = "#1a1d27"
        border = "#2d3148"
        text = "#e8eaf0"
        muted = "#7b8099"
        accent = "#4f8ef7"
    else:
        bg = "#f5f6fa"
        card_bg = "#ffffff"
        border = "#e2e4ed"
        text = "#1a1d27"
        muted = "#6b7280"
        accent = "#2563eb"

    st.markdown(f"""
    <style>
        /* Global background */
        .stApp {{
            background-color: {bg};
        }}
        /* Remove default Streamlit header padding */
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        /* Header bar */
        .dash-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.2rem 1.8rem;
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }}
        .dash-header-left {{
            display: flex;
            flex-direction: column;
        }}
        .dash-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {text};
            margin: 0;
            letter-spacing: -0.3px;
        }}
        .dash-subtitle {{
            font-size: 0.78rem;
            color: {muted};
            margin: 0.2rem 0 0 0;
        }}
        .dash-initials {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background: {accent};
            color: white;
            font-weight: 700;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            justify-content: center;
            letter-spacing: 0.5px;
        }}
        /* Metric cards */
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .metric-card {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 1.1rem 1.3rem;
        }}
        .metric-label {{
            font-size: 0.72rem;
            font-weight: 600;
            color: {muted};
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 0.4rem;
        }}
        .metric-value {{
            font-size: 1.55rem;
            font-weight: 700;
            color: {text};
            letter-spacing: -0.5px;
        }}
        .metric-delta-pos {{
            font-size: 0.78rem;
            font-weight: 600;
            color: #1D9E75;
            margin-top: 0.25rem;
        }}
        .metric-delta-neg {{
            font-size: 0.78rem;
            font-weight: 600;
            color: #D85A30;
            margin-top: 0.25rem;
        }}
        /* Chart containers */
        .chart-card {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 1rem 1.2rem 0.5rem;
            margin-bottom: 1rem;
        }}
        /* Footer */
        .dash-footer {{
            text-align: center;
            font-size: 0.72rem;
            color: {muted};
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid {border};
        }}
        /* Hide Streamlit elements */
        #MainMenu, footer, header {{visibility: hidden;}}
        .stDeployButton {{display: none;}}
    </style>
    """, unsafe_allow_html=True)

    return {
        "bg": bg, "card_bg": card_bg, "border": border,
        "text": text, "muted": muted, "accent": accent,
        "plotly_template": "plotly_dark" if dark else "plotly_white"
    }


# ── DB ────────────────────────────────────────────────────────────────────────
def get_engine():
    return create_engine(
        "postgresql+psycopg2://",
        connect_args={
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT")),
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }
    )


@st.cache_data(ttl=3600)
def load_data():
    engine = get_engine()
    df = pd.read_sql("""
        SELECT * FROM mart_indicators
        ORDER BY open_time DESC
        LIMIT 200
    """, engine)
    df["open_time"] = pd.to_datetime(df["open_time"])
    return df.sort_values("open_time")


# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Settings")
    lang = st.selectbox("", ["EN", "DE"], label_visibility="collapsed")
    dark_mode = st.toggle("Dark mode", value=True)
    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem; color:#7b8099;'>trading_pipeline v1.0<br>Claude Sonafouo</div>",
        unsafe_allow_html=True
    )

T = TRANSLATIONS[lang]
theme = apply_theme(dark_mode)

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_data()

if df.empty:
    st.error(T["no_data"])
    st.stop()

latest = df.iloc[-1]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <div class="dash-header-left">
        <p class="dash-title">{T["title"]}</p>
        <p class="dash-subtitle">{T["subtitle"]}</p>
    </div>
    <div class="dash-initials">SC</div>
</div>
""", unsafe_allow_html=True)

# ── Metric cards ──────────────────────────────────────────────────────────────
delta = latest["price_change_pct"]
delta_class = "metric-delta-pos" if delta >= 0 else "metric-delta-neg"
delta_sign = "+" if delta >= 0 else ""

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-label">{T["current_price"]}</div>
        <div class="metric-value">${latest["close"]:,.2f}</div>
        <div class="{delta_class}">{delta_sign}{delta:.2f}%</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">{T["sma7"]}</div>
        <div class="metric-value">${latest["sma_7"]:,.2f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">{T["sma20"]}</div>
        <div class="metric-value">${latest["sma_20"]:,.2f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">{T["volume"]}</div>
        <div class="metric-value">{latest["volume"]:,.2f} BTC</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Candlestick chart ─────────────────────────────────────────────────────────
st.markdown('<div class="chart-card">', unsafe_allow_html=True)

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["open_time"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="BTC/USDT",
    increasing_line_color="#1D9E75",
    decreasing_line_color="#D85A30"
))

fig.add_trace(go.Scatter(
    x=df["open_time"], y=df["sma_7"],
    mode="lines", name=T["sma7"],
    line=dict(color="#4f8ef7", width=1.5)
))

fig.add_trace(go.Scatter(
    x=df["open_time"], y=df["sma_20"],
    mode="lines", name=T["sma20"],
    line=dict(color="#EF9F27", width=1.5)
))

fig.update_layout(
    title=dict(text=T["chart_title"], font=dict(size=14)),
    xaxis_title=T["time"],
    yaxis_title=T["price"],
    xaxis_rangeslider_visible=False,
    height=460,
    template=theme["plotly_template"],
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── Price change bar chart ────────────────────────────────────────────────────
st.markdown('<div class="chart-card">', unsafe_allow_html=True)

colors = ["#056446" if x >= 0 else "#9E2801"
          for x in df["price_change_pct"].fillna(0)]

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=df["open_time"],
    y=df["price_change_pct"],
    marker_color=colors,
    name=T["chart2_title"]
))

fig2.update_layout(
    title=dict(text=T["chart2_title"], font=dict(size=14)),
    xaxis_title=T["time"],
    yaxis_title=T["change"],
    height=280,
    template=theme["plotly_template"],
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=40, b=10),
    showlegend=False
)

st.plotly_chart(fig2, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander(T["raw_data"]):
    st.dataframe(
        df[["open_time", "open", "high", "low", "close",
            "volume", "sma_7", "sma_20", "price_change_pct"]]
        .tail(50).sort_values("open_time", ascending=False),
        use_container_width=True
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-footer">
    {T["built_by"]} Claude Sonafouo &nbsp;|&nbsp; TU Dortmund &nbsp;|&nbsp;
    github.com/Claudeodg &nbsp;|&nbsp; {T["pipeline"]}
</div>
""", unsafe_allow_html=True)