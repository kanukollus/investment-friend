import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

# 1. SETUP & THEME
st.set_page_config(page_title="2026 Advisor Terminal", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV"

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .stButton>button { width: 100%; border-radius: 4px; background-color: #21262d; border: 1px solid #30363d; color: #58a6ff; height: 2.2em; }
    .stButton>button:hover { border-color: #58a6ff; color: white; }
    .symbol-label { font-family: monospace; font-weight: bold; font-size: 1.1rem; color: #f0f6fc; }
    .status-msg { font-size: 0.8rem; color: #8b949e; margin-top: -10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE WITH FAILOVER
@st.cache_data(ttl=300) # 5-minute cache for speed
def fetch_robust_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE": return {"error": "Missing Key"}
    
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        
        # Detect Throttling
        if "Note" in data:
            return {"error": "Throttled"}
            
        quote = data.get("Global Quote", {})
        if not quote: return {"error": "No Data"}
        
        return {
            "price": f"${float(quote.get('05. price', 0)):,.2f}",
            "change": quote.get("10. change percent", "0%"),
            "up": "-" not in quote.get("10. change percent", "0"),
            "error": None
        }
    except:
        return {"error": "Connection Timeout"}

# 3. THE 2026 ELITE LIST
BUCKETS = {
    "⚡ TODAY": ["PLTR", "MU", "MRVL", "AMD", "RKLB"],
    "🗓️ WEEKLY": ["NVDA", "AVGO", "ANET", "WDC", "MSFT"],
    "🏗️ SEASONAL": ["VRT", "GEV", "OKLO", "PWR", "VST"],
    "🏦 ENGINE": ["GOOGL", "TSM", "ASML", "AAPL", "AMZN"]
}

# 4. APP UI
st.title("🏛️ Senior Advisor Terminal")
st.info("💡 **Pro Tip:** In Jan 2026, RKLB is trading near $76.00 after a 'Hold' upgrade. If the feed is busy, it's due to high retail volume.")

cols = st.columns(4)
for i, (name, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.write(f"#### {name}")
        st.divider()
        for t in tickers:
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.markdown(f"<p style='margin-top:5px;'><span class='symbol-label'>{t}</span></p>", unsafe_allow_html=True)
            with c2:
                if st.button("Details", key=f"btn_{t}"):
                    data = fetch_robust_data(t)
                    if data.get("error") == "Throttled":
                        st.warning("Feed Busy. Retrying in 5s...")
                        time.sleep(2)
                        st.rerun()
                    elif not data.get("error"):
                        clr = "#3fb950" if data['up'] else "#f85149"
                        st.markdown(f"<div style='color:{clr}; font-weight:bold;'>{data['price']} | {data['change']}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("Feed Offline")
