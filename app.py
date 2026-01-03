import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# 1. Page Configuration MUST be the first Streamlit command
st.set_page_config(page_title="Investment Friend 2026", layout="wide", page_icon="🚀")

# 2. Modern Caching Logic (Fixed NameError)
# We use a custom User-Agent to make the server look like a person's browser
@st.cache_data(ttl=3600)
def fetch_market_data(ticker):
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        yf_ticker = yf.Ticker(ticker, session=session)
        # Pulling 1 month for the chart, but we'll use the last 2 days for metrics
        hist = yf_ticker.history(period="1mo")
        return hist if not hist.empty else None
    except Exception:
        return None

# 3. Aggressive Strategy Definitions
STRATEGY = {
    "TODAY": {"ticker": "MU", "note": "High Volatility Scalp", "moat": "HBM4 AI Memory Lead"},
    "WEEK": {"ticker": "NVDA", "note": "Institutional Swing", "moat": "CUDA Software Lock-in"},
    "SEASON": {"ticker": "VRT", "note": "Infrastructure Trend", "moat": "Thermal Management Dominance"},
    "ENGINE": {"ticker": "TSM", "note": "The Wealth Engine", "moat": "2nm Foundry Monopoly"}
}

# Initialize Session Memory
if 'active_view' not in st.session_state:
    st.session_state.active_view = None

# 4. Header & Advisor Note
st.title("🏛️ Senior Advisor Terminal")
st.markdown("""
<div style="background-color: #1f2428; border-left: 5px solid #238636; padding: 20px; border-radius: 8px;">
    <b>Advisor's 2026 Outlook:</b> Aggressive stance remains. We are buying the "Physicality of AI" 
    bottlenecks: Memory, Power, and Foundries.
</div>
""", unsafe_allow_html=True)

# 5. The Dashboard Cards
st.write("### The Four Horizons")
cols = st.columns(4)

for i, (horizon, info) in enumerate(STRATEGY.items()):
    with cols[i]:
        hist = fetch_market_data(info['ticker'])
        if hist is not None:
            price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((price - prev_price) / prev_price) * 100
            st.metric(label=f"{horizon}: {info['ticker']}", value=f"${price:,.2f}", delta=f"{change:.2f}%")
        else:
            st.error(f"Waiting for {info['ticker']} Feed...")
        
        if st.button(f"Analyze {info['ticker']}", key=f"btn_{horizon}"):
            st.session_state.active_view = horizon

# 6. Deep Dive Panel
if st.session_state.active_view:
    view = st.session_state.active_view
    ticker = STRATEGY[view]['ticker']
    hist = fetch_market_data(ticker)
    
    st.divider()
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader(f"🔍 {ticker} Strategic Analysis")
        if hist is not None:
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], 
                            high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig, use_container_width=True)
            
    with col_right:
        st.info(f"**Advisor Logic for {ticker}**")
        st.write(f"**Primary Moat:** {STRATEGY[view]['moat']}")
        st.write(f"**Execution:** {STRATEGY[view]['note']}")
        if st.button("Close Deep Dive"):
            st.session_state.active_view = None
            st.rerun()
