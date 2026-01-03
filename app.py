import streamlit as st
import pandas as pd
import requests
import time

# 1. Page Config
st.set_page_config(page_title="Investment Friend 2026", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV" # <--- REPLACE WITH YOUR KEY

# 2. Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1f2428; color: #58a6ff; border: 1px solid #30363d; }
    .stButton>button:hover { border-color: #238636; color: white; }
    .price-box { background-color: #161b22; padding: 10px; border-radius: 5px; border: 1px solid #238636; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 3. Data Engine (The 'Lazy Fetcher')
def fetch_price(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE":
        return "Key Missing", "0%"
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        data = requests.get(url).json().get("Global Quote", {})
        price = data.get("05. price", "0.00")
        change = data.get("10. change percent", "0%")
        return f"${float(price):,.2f}", change
    except:
        return "Limit Hit", "0%"

# 4. Buckets
BUCKETS = {
    "⚡ TODAY": ["MU", "AMD", "PLTR", "CIFR", "APLD", "SOFI", "RKLB", "MARA", "SMCI", "TSLA"],
    "🗓️ WEEKLY": ["NVDA", "AVGO", "MSFT", "TTD", "META", "BULL", "ADBE", "SNOW", "CRWD", "TEAM"],
    "🏗️ SEASONAL": ["VRT", "PWR", "GEV", "STRL", "EME", "MTZ", "J", "DY", "ENB", "COP"],
    "🏦 ENGINE": ["TSM", "ASML", "AAPL", "AMZN", "LRCX", "GOOGL", "KLAC", "ADI", "NEE", "CVX"]
}

# 5. UI Logic
st.title("🏛️ Senior Advisor Terminal")
st.info("💡 **How to use:** Click a stock to fetch its live 2026 price. This protects your free API limit.")

cols = st.columns(4)

for i, (name, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.subheader(name)
        for t in tickers:
            # Create a unique key for each button
            if st.button(f"Analyze {t}", key=f"btn_{t}"):
                price, change = fetch_price(t)
                st.markdown(f"""
                <div class="price-box">
                    <b style="font-size: 1.2em;">{t}: {price}</b><br>
                    <span style="color: {'#238636' if '+' in change else '#da3633'}">{change}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write(f"• {t}")

st.divider()
st.caption("Status: Aggressive Default Mode | Data Feed: Alpha Vantage (2026 Version)")
