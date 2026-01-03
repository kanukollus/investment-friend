import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Memory and Page Config
if 'active_view' not in st.session_state:
    st.session_state.active_view = None

st.set_page_config(page_title="Investment Friend Pro", layout="wide", page_icon="📈")

# 2. THE FIX: Cached Data Engine
# This function saves the data for 1 hour (3600 seconds) to avoid rate limits
@st.cache_data(ttl=3600)
def fetch_market_data(ticker):
    try:
        # We fetch the ticker object
        yf_ticker = yf.Ticker(ticker)
        # We pull the last 5 days to calculate a delta/change
        hist = yf_ticker.history(period="5d")
        if hist.empty:
            return None
        return hist
    except Exception as e:
        return None

# 3. Strategy Definitions
STRATEGY = {
    "TODAY": {"ticker": "MU", "setup": "Scalp the $315 level. Look for high-volume breakout.", "moat": "Dominant in HBM4 memory chips for AI."},
    "WEEK": {"ticker": "NVDA", "setup": "Swing trade. Target: $210.00.", "moat": "The king of the AI GPU ecosystem."},
    "SEASON": {"ticker": "VRT", "setup": "6-month hold. Power cooling is the 2026 bottleneck.", "moat": "Leader in data center thermal management."},
    "ENGINE": {"ticker": "TSM", "setup": "Wealth engine. Buy every dip below $310.", "moat": "The only foundry for 2nm mass production."}
}

# 4. Dashboard UI
st.title("🏛️ Senior Advisor Terminal")
st.info("Current Stance: **Aggressive**. Data refreshes hourly to protect API limits.")

cols = st.columns(4)
for i, (horizon, info) in enumerate(STRATEGY.items()):
    with cols[i]:
        hist = fetch_market_data(info['ticker'])
        
        if hist is not None:
            price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((price - prev_price) / prev_price) * 100
            
            st.subheader(horizon)
            st.metric(label=info['ticker'], value=f"${price:,.2f}", delta=f"{change:.2f}%")
        else:
            st.error(f"Data Paused for {info['ticker']}")

        if st.button(f"Analyze {info['ticker']}", key=f"btn_{horizon}"):
            st.session_state.active_view = horizon

# 5. Deep Dive Panel
if st.session_state.active_view:
    view = st.session_state.active_view
    ticker = STRATEGY[view]['ticker']
    hist = fetch_market_data(ticker)
    
    st.divider()
    st.header(f"🔍 {ticker} Deep Dive")
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        if hist is not None:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], 
                            high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_b:
        st.write(f"**Strategy:** {STRATEGY[view]['setup']}")
        st.write(f"**Moat:** {STRATEGY[view]['moat']}")
        if st.button("Close Panel"):
            st.session_state.active_view = None
            st.rerun()
