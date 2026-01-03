import streamlit as st
import pandas as pd
import requests
import time

# 1. SETUP
st.set_page_config(page_title="2026 Advisor Terminal", layout="wide", page_icon="🚀")
API_KEY = "YOUR_ALPHA_VANTAGE_KEY_HERE" # Put your key here

st.markdown("""
    <style>
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .stAlert { background-color: #1f2428; border: none; color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE SEQUENTIAL DATA ENGINE
@st.cache_data(ttl=600)
def fetch_safe_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE":
        return {"price": 0.0, "change": "0%", "error": "Enter API Key"}
    
    # We add a small delay to respect the '5 calls per minute' rule
    time.sleep(1.2) 
    
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        r = requests.get(url)
        data = r.json()
        
        # Check for Rate Limit Note
        if "Note" in data:
            return {"price": 0.0, "change": "0%", "error": "Rate Limit (Wait 60s)"}
            
        quote = data.get("Global Quote", {})
        if not quote or "05. price" not in quote:
            return {"price": 0.0, "change": "0%", "error": "Ticker Busy"}
            
        return {
            "price": float(quote.get("05. price", 0)),
            "change": quote.get("10. change percent", "0.00%"),
            "error": None
        }
    except Exception:
        return {"price": 0.0, "change": "0%", "error": "Connection Lost"}

# 3. PORTFOLIO STRATEGY
STRATEGY = {
    "TODAY": {"ticker": "MU", "desc": "AI Memory Scalp"},
    "WEEK": {"ticker": "NVDA", "desc": "GPU Infrastructure"},
    "SEASON": {"ticker": "VRT", "symbol": "VRT", "desc": "Power/Cooling"},
    "ENGINE": {"ticker": "TSM", "desc": "Foundry Moat"}
}

# 4. DASHBOARD UI
st.title("🏛️ Senior Advisor Terminal")
st.info("Status: **Aggressive Strategy Mode** | Active 2026 Cycle")

if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE":
    st.warning("👈 Please paste your Alpha Vantage Key into the code to activate live data.")

cols = st.columns(4)

for i, (horizon, info) in enumerate(STRATEGY.items()):
    with cols[i]:
        # Sequentially fetch data
        data = fetch_safe_data(info['ticker'])
        
        st.subheader(horizon)
        if data['error']:
            st.error(f"{info['ticker']}: {data['error']}")
            st.metric(label=info['ticker'], value="---", delta="Paused")
        else:
            st.metric(label=info['ticker'], value=f"${data['price']:,.2f}", delta=data['change'])
        
        st.caption(info['desc'])

# 5. THE MANUAL REBOOT (To Clear 'Zeroes')
st.divider()
if st.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()
