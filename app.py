import streamlit as st
import pandas as pd
import requests
import time

# 1. SETUP
st.set_page_config(page_title="2026 Advisor Terminal", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV"  # Use your key!

st.markdown("""
    <style>
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE WITH COOLDOWN
@st.cache_data(ttl=600)
def fetch_stock_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE":
        return {"price": "0.00", "change": "0%", "error": "Missing API Key"}
    
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        
        # If we hit the rate limit (5 calls/min), Alpha Vantage returns a 'Note'
        if "Note" in data:
            return {"price": "0.00", "change": "0%", "error": "Rate Limit Hit"}
            
        quote = data.get("Global Quote", {})
        if not quote:
            return {"price": "0.00", "change": "0%", "error": "Ticker Not Found"}
            
        return {
            "price": quote.get("05. price", "0.00"),
            "change": quote.get("10. change percent", "0.00%"),
            "error": None
        }
    except Exception as e:
        return {"price": "0.00", "change": "0%", "error": str(e)}

# 3. STRATEGY
STRATEGY = {
    "TODAY": {"ticker": "MU", "desc": "Memory/AI Momentum"},
    "WEEK": {"ticker": "NVDA", "desc": "GPU Dominance"},
    "SEASON": {"ticker": "VRT", "desc": "Power Infrastructure"},
    "ENGINE": {"ticker": "TSM", "desc": "Foundry Monopoly"}
}

# 4. DASHBOARD
st.title("🏛️ Senior Advisor Terminal")
st.write("Status: 🟢 **Aggressive Strategy Live** (Jan 2026)")

cols = st.columns(4)

for i, (horizon, info) in enumerate(STRATEGY.items()):
    with cols[i]:
        # Add a tiny 0.5s delay to prevent hitting the 5-calls-per-minute limit too fast
        time.sleep(0.5) 
        
        data = fetch_stock_data(info['ticker'])
        
        st.subheader(horizon)
        if data['error']:
            st.warning(f"{info['ticker']}: {data['error']}")
            st.metric(label=info['ticker'], value="---", delta="Paused")
        else:
            price_val = float(data['price'])
            st.metric(label=info['ticker'], value=f"${price_val:,.2f}", delta=data['change'])
        
        st.caption(info['desc'])

st.divider()
st.info("💡 **Advisor Tip:** If you see 'Rate Limit Hit', wait 60 seconds and refresh. The free Alpha Vantage key allows 5 checks per minute.")
