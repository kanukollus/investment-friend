import streamlit as st
import pandas as pd
import requests
import time

# 1. SETUP
st.set_page_config(page_title="Investment Friend: Power 40", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV"

# 2. DATA ENGINE
@st.cache_data(ttl=600)
def fetch_top_pick(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE": return None
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        data = requests.get(url).json().get("Global Quote", {})
        return {"price": data.get("05. price", "0.00"), "change": data.get("10. change percent", "0%")}
    except: return None

# 3. BUCKET DEFINITIONS (10 STOCKS EACH)
BUCKETS = {
    "⚡ TODAY (24h)": ["MU", "AMD", "PLTR", "CIFR", "APLD", "SOFI", "RKLB", "MARA", "SMCI", "TSLA"],
    "🗓️ THIS WEEK (7d)": ["NVDA", "AVGO", "MSFT", "TTD", "META", "BULL", "ADBE", "SNOW", "CRWD", "TEAM"],
    "🏗️ THIS SEASON (6mo)": ["VRT", "PWR", "GEV", "STRL", "EME", "MTZ", "J", "DY", "ENB", "COP"],
    "🏦 THE ENGINE (5yr)": ["TSM", "ASML", "AAPL", "AMZN", "LRCX", "GOOGL", "KLAC", "ADI", "NEE", "CVX"]
}

# 4. DASHBOARD UI
st.title("🏛️ 2026 Senior Advisor Terminal")
st.subheader("Aggressive Stance: The 'Physicality of AI' Cycle")

cols = st.columns(4)

for i, (name, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.write(f"### {name}")
        
        # Display the Lead Stock with live data
        lead = tickers[0]
        data = fetch_top_pick(lead)
        if data:
            st.metric(label=f"LEAD: {lead}", value=f"${float(data['price']):.2f}", delta=data['change'])
        
        st.write("**Top 10 Watchlist:**")
        for t in tickers:
            st.markdown(f"- **{t}**")

# 5. THE ADVISOR'S INTERPRETATION (The 'Why')
st.divider()
col_a, col_b = st.columns(2)
with col_a:
    st.info("💡 **What this means for your friends:**")
    st.write("""
    - **TODAY:** These stocks have high 'Beta' (volatility). They move 5-10% a day. Great for fast cash, but requires a stop-loss.
    - **WEEK:** These are 'Catalyst' plays. We expect news (earnings, product launches) to move these by Friday.
    """)
with col_b:
    st.write("""
    - **SEASON:** These are 'Macro' plays. High-interest rates or government infrastructure spending drives these over months.
    - **ENGINE:** These are 'Moat' plays. These are the companies your grandkids will own. Buy and forget.
    """)
