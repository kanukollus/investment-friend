import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. PREMIUM TRADING UI
st.set_page_config(page_title="2026 Strike Zone Terminal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .signal-box { padding: 15px; border-radius: 8px; margin-top: 10px; font-family: monospace; }
    .buy-signal { background-color: #062512; border: 1px solid #238636; color: #3fb950; }
    .target-text { color: #58a6ff; font-weight: bold; }
    .stop-text { color: #f85149; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE SIGNAL ENGINE (Pivot Point Logic)
@st.cache_data(ttl=600)
def get_trade_setup(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Get yesterday's data for pivot calculations
        hist = stock.history(period="2d")
        if len(hist) < 2: return None
        
        prev = hist.iloc[-2]  # Yesterday
        curr = hist.iloc[-1]  # Today (so far)
        
        high = prev['High']
        low = prev['Low']
        close = prev['Close']
        
        # Standard Pivot Point Calculation
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        
        return {
            "price": curr['Close'],
            "change": ((curr['Close'] - prev['Close']) / prev['Close']) * 100,
            "entry": s1,
            "target": r1,
            "stop": s1 * 0.985  # 1.5% Tight Stop for Day Trading
        }
    except: return None

# 3. GLOBAL RANKER (From v4.0)
@st.cache_data(ttl=86400)
def get_ranked_symbols():
    titans = ["NVDA", "TSLA", "PLTR", "MU", "AMD", "META", "AVGO", "MSFT", "AAPL", "GOOGL"]
    return titans

# 4. DASHBOARD
st.title("🎯 Day Trade: Strike Zone")
st.markdown("### ⚡ Today's Momentum Leaders")
st.caption("Signals based on Institutional Pivot Points | Cycle: Jan 3, 2026")

symbols = get_ranked_symbols()
cols = st.columns(5)

if 'unlocked_trade' not in st.session_state:
    st.session_state.unlocked_trade = "NVDA"

# Horizontal Row for Top 5
for i, t in enumerate(symbols[:5]):
    with cols[i]:
        if st.session_state.unlocked_trade == t:
            setup = get_trade_setup(t)
            if setup:
                st.metric(label=t, value=f"${setup['price']:.2f}", delta=f"{setup['change']:.2f}%")
                st.markdown(f"""
                    <div class="signal-box buy-signal">
                        <b>STRATEGY: SCALP</b><br>
                        Entry: ${setup['entry']:.2f}<br>
                        <span class="target-text">Target: ${setup['target']:.2f}</span><br>
                        <span class="stop-text">Stop: ${setup['stop']:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.metric(label=t, value="--", delta="Locked")
            if st.button(f"Analyze {t}", key=f"trd_{t}"):
                st.session_state.unlocked_trade = t
                st.rerun()

# 5. EXECUTION GUIDE
st.divider()
st.subheader("🏛️ Execution Rules for Day Trading Profit")

c1, c2, c3 = st.columns(3)
with c1:
    st.info("**1. The Entry**\nOnly enter if the price touches the 'Entry' level. If it's already above the Target, the trade is 'overextended'—do not chase it.")
with c2:
    st.success("**2. The Target**\nOnce the price hits the 'Target' level, sell 75% of your position. Let the remaining 25% run with a trailing stop.")
with c3:
    st.error("**3. The Stop**\nIf the price hits the 'Stop' level, exit immediately. No emotions. In 2026, a 1.5% move against you often signals a trend reversal.")
