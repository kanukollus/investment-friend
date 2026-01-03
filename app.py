import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# 1. PAGE SETUP & ELITE CSS
st.set_page_config(page_title="2026 Sovereign Terminal", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV"

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    /* Metric Card Styling */
    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #161b22;
        border-radius: 5px 5px 0 0;
        gap: 1px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #21262d; border-bottom: 2px solid #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE
@st.cache_data(ttl=600)
def fetch_ticker_lite(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE": return {"price": "0.00", "change": "0%", "up": True}
    try:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
        data = requests.get(url).json().get("Global Quote", {})
        return {
            "price": f"${float(data.get('05. price', 0)):,.2f}",
            "change": data.get("10. change percent", "0%"),
            "up": "-" not in data.get("10. change percent", "0")
        }
    except: return {"price": "Busy", "change": "0%", "up": True}

# 3. THE 2026 ELITE BUCKETS
BUCKETS = {
    "⚡ TODAY": ["PLTR", "MU", "MRVL", "AMD", "RKLB"],
    "🗓️ WEEKLY": ["NVDA", "AVGO", "ANET", "WDC", "MSFT"],
    "🏗️ SEASONAL": ["VRT", "GEV", "OKLO", "PWR", "VST"],
    "🏦 ENGINE": ["GOOGL", "TSM", "ASML", "AAPL", "AMZN"]
}

# 4. HEADER
st.title("🏛️ Sovereign Advisor Terminal")
st.markdown("<p style='color: #8b949e;'>Portfolio Intelligence | Cycle: Agentic AI Integration</p>", unsafe_allow_html=True)

# 5. DEFAULT EXPANDED: TODAY (Horizontal Layout)
st.write("### ⚡ Current Scalps (Today's Focus)")
today_cols = st.columns(5)
for idx, ticker in enumerate(BUCKETS["⚡ TODAY"]):
    with today_cols[idx]:
        data = fetch_ticker_lite(ticker)
        st.metric(label=ticker, value=data['price'], delta=data['change'])
        if st.button(f"Analyze {ticker}", key=f"today_{ticker}"):
            st.session_state.active_ticker = ticker

# 6. TABS FOR OTHER HORIZONS
st.divider()
tab_week, tab_season, tab_engine = st.tabs(["🗓️ Weekly Swings", "🏗️ Seasonal Macro", "🏦 The Engine (Long)"])

with tab_week:
    cols = st.columns(5)
    for idx, t in enumerate(BUCKETS["🗓️ WEEKLY"]):
        with cols[idx]:
            if st.button(f"Load {t}", key=f"wk_{t}"):
                data = fetch_ticker_lite(t)
                st.metric(label=t, value=data['price'], delta=data['change'])
                st.session_state.active_ticker = t

with tab_season:
    cols = st.columns(5)
    for idx, t in enumerate(BUCKETS["🏗️ SEASONAL"]):
        with cols[idx]:
            if st.button(f"Load {t}", key=f"sn_{t}"):
                data = fetch_ticker_lite(t)
                st.metric(label=t, value=data['price'], delta=data['change'])
                st.session_state.active_ticker = t

with tab_engine:
    cols = st.columns(5)
    for idx, t in enumerate(BUCKETS["🏦 ENGINE"]):
        with cols[idx]:
            if st.button(f"Load {t}", key=f"eng_{t}"):
                data = fetch_ticker_lite(t)
                st.metric(label=t, value=data['price'], delta=data['change'])
                st.session_state.active_ticker = t

# 7. FOOTER BRIEFING
st.divider()
st.info("💡 **Advisor Strategy:** In 2026, we are watching **PLTR** (Palantir) as it becomes the 'Operating System' for autonomous business agents. It remains the anchor of our TODAY bucket.")
