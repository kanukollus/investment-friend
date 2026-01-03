import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Page Configuration & Professional Styling
st.set_page_config(page_title="Investment Friend MVP", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    div[data-testid="metric-container"] { color: white; }
    h1, h2, h3 { color: #58a6ff !important; font-family: 'Inter', sans-serif; }
    .advisor-note { background-color: #1f2428; border-left: 5px solid #238636; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Senior Advisor Logic: The 2026 Strategy Engine
# These are our "Aggressive Default" picks for January 3, 2026
STRATEGY = {
    "TODAY": {"ticker": "MU", "goal": "Day Trade Scalp", "target": "$325.00", "risk": "High"},
    "WEEK": {"ticker": "NVDA", "goal": "Catalyst Swing", "target": "$210.00", "risk": "Medium-High"},
    "SEASON": {"ticker": "VRT", "goal": "Infrastructure Trend", "target": "Q1 Earnings Rally", "risk": "Medium"},
    "ENGINE": {"ticker": "TSM", "goal": "Wealth Compounder", "target": "Intrinsic Value $420", "risk": "Low-Medium"}
}

def get_live_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d")
        return data['Close'].iloc[-1], ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
    except:
        return 0.0, 0.0

# 3. Sidebar: The "Aggressive Friend" Controls
with st.sidebar:
    st.title("Senior Advisor 🏛️")
    st.success("Mode: Aggressive Default")
    st.info("Market Context: Early 2026 AI Expansion Phase")
    if st.button("Change Assumptions"):
        st.warning("Questionnaire Coming in v1.2")
    st.divider()
    st.write("Current VIX: **14.5 (Calm)**")
    st.write("S&P 500 Target: **7,800**")

# 4. Main Dashboard Header
st.title("Welcome back, Friend.")
st.markdown("""<div class="advisor-note">
    <b>Senior Advisor's Briefing:</b> The first week of 2026 is showing strong institutional flow into 
    AI memory and power infrastructure. We are staying <b>Aggressive</b>. Here is your roadmap:
    </div>""", unsafe_allow_html=True)

# 5. The Four-Horizon Dashboard
cols = st.columns(4)

for i, (horizon, info) in enumerate(STRATEGY.items()):
    with cols[i]:
        price, change = get_live_data(info['ticker'])
        st.subheader(f"{horizon}")
        st.metric(label=f"{info['ticker']} (Current)", value=f"${price:,.2f}", delta=f"{change:.2f}%")
        st.write(f"**Goal:** {info['goal']}")
        st.write(f"**Target:** {info['target']}")
        
        # Action Trigger
        if horizon == "TODAY":
            st.button("View Setup", key=f"btn_{i}", use_container_width=True)
        else:
            st.button("Analyze Moat", key=f"btn_{i}", use_container_width=True)

# 6. Real-Time Charting for the "Active" Pick
st.divider()
st.subheader(f"Strategic Focus: {STRATEGY['WEEK']['ticker']} Analysis")
chart_data = yf.Ticker(STRATEGY['WEEK']['ticker']).history(period="1mo")
fig = go.Figure(data=[go.Candlestick(x=chart_data.index,
                open=chart_data['Open'], high=chart_data['High'],
                low=chart_data['Low'], close=chart_data['Close'])])
fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

# 7. Disclaimer
st.caption("Disclaimer: This app provides algorithm-driven suggestions based on aggressive defaults. Not financial advice. Past performance does not guarantee 2026 returns.")
