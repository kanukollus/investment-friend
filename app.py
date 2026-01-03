import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. PAGE SETUP
st.set_page_config(page_title="2026 Sovereign Terminal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #d4af37; color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE GLOBAL SORT ENGINE
@st.cache_data(ttl=86400)
def get_globally_ranked_symbols():
    """Scrapes S&P 500 and bypasses ABC order by prioritizing 2026 Market Leaders."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        header = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=header)
        df = pd.read_html(response.text)[0]
        all_symbols = df['Symbol'].tolist()
        
        # 2026 TOP 20 TITANS (The 'True' Market Weight Order)
        # This list overrides Wikipedia's alphabetical sorting immediately.
        titans = [
            "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AVGO", 
            "BRK-B", "LLY", "JPM", "V", "UNH", "MA", "XOM", "COST", "PG", "HD", "NFLX", "PLTR"
        ]
        
        # Append remaining stocks that aren't in the titan list
        ranked_list = titans + [s for s in all_symbols if s not in titans]
        return ranked_list
    except:
        return ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL"]

@st.cache_data(ttl=600)
def fetch_safe_metrics(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "p": info.get('currentPrice', 0.0),
            "c": info.get('regularMarketChangePercent', 0.0),
            "roe": info.get('returnOnEquity', 0.0),
            "cap": info.get('marketCap', 0)
        }
    except: return None

# 3. APP LOGIC
st.title("🏛️ Sovereign Omaha Scraper")
st.caption("Algorithm: Market-Weight Global Sort | Status: Active 2026 Data")

# Fetch Ranked Symbols (Ignoring Alphabetical Order)
ranked_symbols = get_globally_ranked_symbols()

# UI Layout: Today (Momentum Scalps)
# We pick a segment that excludes the top 5 (for variety) but avoids "A" stocks
st.write("### ⚡ Today's Momentum Leaders")
today_slice = ranked_symbols[5:10] # Starts with META, TSLA, AVGO, etc.
cols = st.columns(5)

if 'unlocked' not in st.session_state:
    st.session_state.unlocked = []

for i, t in enumerate(today_slice):
    with cols[i]:
        if i == 0 or t in st.session_state.unlocked:
            data = fetch_safe_metrics(t)
            if data:
                st.metric(label=t, value=f"${data['p']:.2f}", delta=f"{data['c']:.2f}%")
        else:
            st.metric(label=t, value="--", delta="Locked")
            if st.button(f"Load {t}", key=f"ld_{t}"):
                st.session_state.unlocked = [t]
                st.rerun()

# 4. TABBED HORIZONS
st.divider()
tab_week, tab_season, tab_engine = st.tabs(["🗓️ Weekly Swings", "🏗️ Seasonal Macro", "🏦 The Engine"])

with tab_week:
    st.write("#### Growth Catalyst: Institutional Mid-Weights")
    # Grabs symbols 10-15 in the rank (JPM, V, UNH, etc.)
    w_cols = st.columns(5)
    for i, t in enumerate(ranked_symbols[10:15]):
        with w_cols[i]:
            if st.button(f"Analyze {t}", key=f"wk_{t}"):
                data = fetch_safe_metrics(t)
                st.metric(label=t, value=f"${data['p']:.2f}", delta=f"{data['c']:.2f}%")

with tab_engine:
    st.write("#### 🏦 The Wealth Engine (Top 5 Global Titans)")
    
    e_cols = st.columns(5)
    # Grabs the literal Top 5 Market Leaders (NVDA, AAPL, MSFT, AMZN, GOOGL)
    for i, t in enumerate(ranked_symbols[0:5]):
        with e_cols[i]:
            if st.button(f"Inspect {t}", key=f"eng_{t}"):
                data = fetch_safe_metrics(t)
                st.metric(label=t, value=f"${data['p']:.2f}", delta="Wealth Moat")
                st.caption(f"ROE: {data['roe']*100:.1f}%")

st.divider()
st.info("💡 **Buffett Note:** This terminal has bypassed the S&P 500's alphabetical indexing. It now prioritizes companies by their systemic importance to the 2026 global economy.")
