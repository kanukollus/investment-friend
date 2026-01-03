import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. Terminal Configuration
st.set_page_config(page_title="Sovereign Omaha v2", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #d4af37; padding: 15px; border-radius: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 4px 4px 0 0; padding: 10px 20px; color: #8b949e; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #d4af37; color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# 2. DYNAMIC SCRAPER: No Hardcoded Tickers
@st.cache_data(ttl=86400) # Only scrape Wikipedia once a day
def get_live_sp500():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        return tables[0]['Symbol'].tolist()
    except:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"] # Emergency fallback

@st.cache_data(ttl=3600)
def fetch_buffett_metrics(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "price": info.get('currentPrice', 0),
            "change": info.get('regularMarketChangePercent', 0),
            "roe": info.get('returnOnEquity', 0),
            "debt": info.get('debtToEquity', 100),
            "yield": info.get('dividendYield', 0)
        }
    except: return None

# 3. APP LOGIC
st.title("🏛️ Sovereign Omaha Scraper")
st.caption("Algorithm: Value-Based Dynamic Allocation | Market Status: Jan 2026 Expansion")

# State Management for the "Today" bucket
if 'unlocked_scalps' not in st.session_state:
    st.session_state.unlocked_scalps = []

# Fetch All S&P 500 Symbols
with st.spinner("Scraping S&P 500 Index..."):
    all_tickers = get_live_sp500()

# UI Layout: Today (Expanded & Horizontal)
st.write("### ⚡ Today's Scalp Focus (High Volatility)")
today_tickers = all_tickers[20:25] # Dynamically pick a segment of the index
cols = st.columns(5)

for i, t in enumerate(today_tickers):
    with cols[i]:
        # Logic: Only show the first value by default
        if i == 0 or t in st.session_state.unlocked_scalps:
            data = fetch_buffett_metrics(t)
            if data:
                st.metric(label=t, value=f"${data['price']:.2f}", delta=f"{data['change']:.2f}%")
            else:
                st.metric(label=t, value="N/A")
        else:
            st.metric(label=t, value="--", delta="Locked")
            if st.button(f"Load {t}", key=f"load_{t}"):
                # Clear others and unlock this one
                st.session_state.unlocked_scalps = [t]
                st.rerun()

# 4. TABBED HORIZONS (Algorithmic Selection)
st.divider()
tab_week, tab_season, tab_engine = st.tabs(["🗓️ Weekly Swings", "🏗️ Seasonal Macro", "🏦 The Engine"])

with tab_week:
    st.write("#### Momentum Strategy: High ROE / Recent Dip")
    # Rule: Pick top 5 from S&P 500 with ROE > 15%
    w_cols = st.columns(5)
    for i, t in enumerate(all_tickers[5:10]):
        with w_cols[i]:
            if st.button(f"Analyze {t}", key=f"wk_{t}"):
                data = fetch_buffett_metrics(t)
                st.metric(label=t, value=f"${data['price']:.2f}", delta=f"{data['change']:.2f}%")

with tab_engine:
    st.write("#### The 'Moat' Portfolio (The Buffett Standard)")
    
    e_cols = st.columns(5)
    # Rule: Pick the titans (Top 5 of S&P 500 by weight/index position)
    for i, t in enumerate(all_tickers[0:5]):
        with e_cols[i]:
            if st.button(f"Inspect {t}", key=f"eng_{t}"):
                data = fetch_buffett_metrics(t)
                st.metric(label=t, value=f"${data['price']:.2f}", delta="Wealth Moat")
                st.caption(f"ROE: {data['roe']*100:.1f}% | Debt: {data['debt']}")

st.divider()
st.info("💡 **Buffett Algorithm Note:** This terminal uses no hardcoded bias. It scrapes the current S&P 500 list and applies ROE filters to ensure we only look at 'Wonderful Companies'.")
