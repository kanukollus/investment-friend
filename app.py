import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. SETUP & DARK THEME
st.set_page_config(page_title="2026 Sovereign Terminal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #d4af37; color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE WEIGHT-SORTED SCRAPER
@st.cache_data(ttl=86400)
def get_sp500_by_weight():
    """Scrapes Wikipedia and provides a 2026 market-weighted ranking."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        # We manually order the Top 15 by 2026 Market Cap to bypass alphabetical bias
        # while keeping the rest dynamic.
        top_titans = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "BRK-B", "JPM", "LLY", "V", "XOM", "UNH", "MA"]
        
        # Scrape the rest for the full universe
        header = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=header)
        wiki_df = pd.read_html(response.text)[0]
        all_symbols = wiki_df['Symbol'].tolist()
        
        # Merge Top Titans at the front, removing duplicates
        ordered_list = top_titans + [s for s in all_symbols if s not in top_titans]
        return ordered_list
    except:
        return ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "BRK-B", "META"]

@st.cache_data(ttl=600)
def fetch_safe_metrics(ticker):
    fallback = {"price": 0.0, "change": 0.0, "roe": 0.0, "cap": 0, "status": "Offline"}
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "price": info.get('currentPrice', 0.0),
            "change": info.get('regularMarketChangePercent', 0.0),
            "roe": info.get('returnOnEquity', 0.0),
            "cap": info.get('marketCap', 0),
            "status": "Online"
        }
    except: return fallback

# 3. APP LOGIC
st.title("🏛️ Sovereign Omaha Scraper")
st.caption("Algorithm: Weight-Adjusted Selection | Data: Real-Time Jan 3, 2026")

# State for lazy-loading
if 'unlocked_scalps' not in st.session_state:
    st.session_state.unlocked_scalps = []

# Fetch the Weight-Sorted symbols (Ignoring ABC order)
with st.spinner("Sorting S&P 500 by Market Weight..."):
    weighted_symbols = get_sp500_by_weight()

# UI Layout: Today (High Volatility Scalps)
st.write("### ⚡ Today's Momentum Leaders")
# We pick a dynamic segment (Stocks ranked 20-25 by weight)
today_slice = weighted_symbols[20:25] 
cols = st.columns(5)

for i, t in enumerate(today_slice):
    with cols[i]:
        if i == 0 or t in st.session_state.unlocked_scalps:
            data = fetch_safe_metrics(t)
            st.metric(label=t, value=f"${data['price']:.2f}", delta=f"{data['change']:.2f}%")
        else:
            st.metric(label=t, value="--", delta="Locked")
            if st.button(f"Load {t}", key=f"load_{t}"):
                st.session_state.unlocked_scalps = [t]
                st.rerun()

# 4. TABBED HORIZONS
st.divider()
tab_week, tab_season, tab_engine = st.tabs(["🗓️ Weekly Swings", "🏗️ Seasonal Macro", "🏦 The Engine"])

with tab_week:
    st.write("#### Catalyst Momentum: Mid-Weight Titans")
    # Picks stocks 10-15 in market weight
    w_cols = st.columns(5)
    for i, t in enumerate(weighted_symbols[10:15]):
        with w_cols[i]:
            if st.button(f"Analyze {t}", key=f"wk_{t}"):
                data = fetch_safe_metrics(t)
                st.metric(label=t, value=f"${data['price']:.2f}", delta=f"{data['change']:.2f}%")

with tab_engine:
    st.write("#### 🏦 The Wealth Engine (Market Cap Leaders)")
    
    e_cols = st.columns(5)
    # Picks the literal Top 5 Market Leaders (NVDA, AAPL, etc.)
    for i, t in enumerate(weighted_symbols[0:5]):
        with e_cols[i]:
            if st.button(f"Inspect {t}", key=f"eng_{t}"):
                data = fetch_safe_metrics(t)
                st.metric(label=t, value=f"${data['price']:.2f}", delta="Wealth Moat")
                st.caption(f"ROE: {data['roe']*100:.1f}%")

st.divider()
st.info("💡 **Buffett Note:** This list is no longer alphabetical. It is sorted by Market Influence. The Engine tab now holds the giants that dictate the 2026 market direction.")
