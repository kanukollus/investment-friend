import streamlit as st
import pandas as pd
import requests
import time

# 1. AUTH & CONFIG
st.set_page_config(page_title="2026 Sovereign Terminal", layout="wide")
API_KEY = "YOUR_ALPHA_VANTAGE_KEY_HERE" 

# 2. THE DYNAMIC DATA ENGINE
@st.cache_data(ttl=300) # Data stays fresh for 5 mins
def get_live_quote(ticker):
    if API_KEY == "ZFVR5I30DHJS6MEV":
        return {"p": "Demo", "c": "0%"}
    
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        # We add a tiny delay to ensure we don't burst the API
        time.sleep(0.2)
        r = requests.get(url, timeout=5)
        data = r.json().get("Global Quote", {})
        if not data: return {"p": "Busy", "c": "0%"}
        return {
            "p": f"${float(data.get('05. price', 0)):,.2f}",
            "c": data.get("10. change percent", "0%")
        }
    except:
        return {"p": "Error", "c": "0%"}

# 3. SESSION STATE (The App's Memory)
if 'active_scalp' not in st.session_state:
    st.session_state.active_scalp = "PLTR"

# 4. CUSTOM UI STYLING
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 12px; }
    .stButton>button { width: 100%; border-radius: 6px; background-color: #21262d; border: 1px solid #30363d; color: #58a6ff; }
    .stButton>button:hover { border-color: #58a6ff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 5. DASHBOARD HEADER
st.title("🏛️ Sovereign Advisor Terminal")
st.markdown("<p style='color: #8b949e;'>Real-Time Market Intelligence | Jan 3, 2026</p>", unsafe_allow_html=True)

# 6. TODAY'S SCALPS (Horizontal Row with Lazy Loading)
st.write("### ⚡ Today's Focus (Click to Unlock)")
tickers = ["PLTR", "MU", "MRVL", "AMD", "RKLB"]
cols = st.columns(5)

for i, t in enumerate(tickers):
    with cols[i]:
        if st.session_state.active_scalp == t:
            # Active stock pulls REAL data from API
            with st.spinner("Fetching..."):
                data = get_live_quote(t)
            st.metric(label=t, value=data['p'], delta=data['c'])
        else:
            # Inactive stocks show placeholders
            st.metric(label=t, value="--", delta="Locked")
        
        if st.button(f"Load {t}", key=f"btn_{t}"):
            st.session_state.active_scalp = t
            st.rerun()

# 7. TABBED INTERFACE FOR LONG-TERM HORIZONS
st.divider()
tab_week, tab_season, tab_engine = st.tabs(["🗓️ Weekly Swings", "🏗️ Seasonal Macro", "🏦 The Engine"])

with tab_week:
    st.info("💡 **Weekly Strategy:** We are tracking **NVDA** as it approaches its Jan 2026 earnings gap. Load below to check current resistance.")
    w_cols = st.columns(5)
    w_tickers = ["NVDA", "AVGO", "ANET", "WDC", "MSFT"]
    for idx, wt in enumerate(w_tickers):
        with w_cols[idx]:
            if st.button(f"Price: {wt}", key=f"wk_{wt}"):
                data = get_live_quote(wt)
                st.metric(label=wt, value=data['p'], delta=data['c'])

with tab_engine:
    st.write("### 🏦 Wealth Generation")
    st.markdown("These are the 'Forever' stocks for the 2026–2030 cycle.")
    e_cols = st.columns(5)
    e_tickers = ["GOOGL", "TSM", "ASML", "AAPL", "AMZN"]
    for idx, et in enumerate(e_tickers):
        with e_cols[idx]:
            if st.button(f"Check {et}", key=f"eng_{et}"):
                data = get_live_quote(et)
                st.metric(label=et, value=data['p'], delta=data['c'])
