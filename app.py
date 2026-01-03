import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Initialize App Memory (Session State)
if 'active_view' not in st.session_state:
    st.session_state.active_view = None
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = None

# 2. Page Styling
st.set_page_config(page_title="Investment Friend Pro", layout="wide", page_icon="📈")
st.markdown("""
    <style>
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .advisor-box { background-color: #1f2428; border-left: 5px solid #238636; padding: 20px; border-radius: 8px; margin-bottom: 25px; }
    .analysis-panel { background-color: #0d1117; border: 1px dashed #58a6ff; padding: 20px; border-radius: 10px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Data Strategy
STRATEGY = {
    "TODAY": {"ticker": "MU", "setup": "Scalp the $315 level. Look for high-volume breakout.", "moat": "Dominant in HBM4 memory chips for AI."},
    "WEEK": {"ticker": "NVDA", "setup": "Swing trade. Accumulate at $185 for a $210 target.", "moat": "The undisputed king of the AI GPU software ecosystem."},
    "SEASON": {"ticker": "VRT", "setup": "6-month hold. Power cooling is the bottleneck of 2026.", "moat": "Global leader in data center thermal management."},
    "ENGINE": {"ticker": "TSM", "setup": "Wealth engine. Buy every dip below $310.", "moat": "The only foundry capable of 2nm mass production."}
}

# 4. Main UI
st.title("🏛️ Senior Advisor Terminal")
st.markdown("<div class='advisor-box'><b>Current Stance: Aggressive.</b> We are prioritizing 'The Physicality of AI' (Memory & Power) over SaaS for Q1 2026.</div>", unsafe_allow_html=True)

cols = st.columns(4)
for i, (horizon, info) in enumerate(STRATEGY.items()):
    with cols[i]:
        # Simple data fetch
        price = yf.Ticker(info['ticker']).history(period="1d")['Close'].iloc[-1]
        st.subheader(horizon)
        st.metric(label=info['ticker'], value=f"${price:,.2f}")
        
        # Button Logic: These now save the choice to memory (Session State)
        if st.button(f"Deep Dive: {info['ticker']}", key=f"btn_{horizon}"):
            st.session_state.active_view = horizon
            st.session_state.active_ticker = info['ticker']

# 5. The "Deep Dive" Panel (Only shows when a button is clicked)
if st.session_state.active_view:
    view = st.session_state.active_view
    ticker = st.session_state.active_ticker
    
    st.divider()
    st.markdown(f"<div class='analysis-panel'><h3>🔍 Analysis for {ticker} ({view} Play)</h3>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.write(f"**Execution Setup:** {STRATEGY[view]['setup']}")
        st.write(f"**Competitive Moat:** {STRATEGY[view]['moat']}")
        
        # Live Charting
        hist = yf.Ticker(ticker).history(period="1mo")
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.info("💡 Senior Advisor Tip")
        st.write(f"In 2026, {ticker} is a core holding. If you are playing the **{view}** horizon, watch the 10-year yield. If it spikes, tighten your stop loss.")
        if st.button("Close Analysis"):
            st.session_state.active_view = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
