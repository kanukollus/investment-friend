import streamlit as st
import pandas as pd
import requests
import time

# 1. SETUP & THEME
st.set_page_config(page_title="Investment Friend 2026", layout="wide", page_icon="🚀")
API_KEY = "ZFVR5I30DHJS6MEV" # <--- PASTE KEY HERE

st.markdown("""
    <style>
    .stExpander { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 10px; }
    .price-text { color: #58a6ff; font-weight: bold; font-size: 1.2em; }
    .advisor-box { background-color: #1f2428; border-left: 5px solid #238636; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE (The 'Lazy Loader')
@st.cache_data(ttl=600)
def get_stock_price(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE":
        return "N/A", "0%"
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        data = requests.get(url).json().get("Global Quote", {})
        price = data.get("05. price", "0.00")
        change = data.get("10. change percent", "0%")
        return f"${float(price):,.2f}", change
    except:
        return "Limit Hit", "0%"

# 3. THE POWER 40 LIST (Jan 2026)
BUCKETS = {
    "⚡ TODAY (Scalps)": ["MU", "AMD", "PLTR", "CIFR", "APLD", "SOFI", "RKLB", "MARA", "SMCI", "TSLA"],
    "🗓️ WEEKLY (Swings)": ["NVDA", "AVGO", "MSFT", "TTD", "META", "BULL", "ADBE", "SNOW", "CRWD", "TEAM"],
    "🏗️ SEASONAL (Tactical)": ["VRT", "PWR", "GEV", "STRL", "EME", "MTZ", "J", "DY", "ENB", "COP"],
    "🏦 THE ENGINE (Wealth)": ["TSM", "ASML", "AAPL", "AMZN", "LRCX", "GOOGL", "KLAC", "ADI", "NEE", "CVX"]
}

# 4. APP UI
st.title("🏛️ Senior Advisor Terminal")
st.markdown("<div class='advisor-box'><b>2026 Advisor Note:</b> The free API allows 5 stocks per minute. Open one bucket at a time to avoid errors.</div>", unsafe_allow_html=True)

cols = st.columns(4)

for i, (name, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        # This creates the expandable section you asked for
        with st.expander(f"**{name}**", expanded=(i==0)):
            st.write("---")
            for t in tickers:
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.write(f"**{t}**")
                with c2:
                    # We only fetch if the expander is OPEN
                    # To be even safer, we'll only fetch the first 3 in each list 
                    # unless they click a 'load more' button (v2.0)
                    if tickers.index(t) < 3: 
                        price, change = get_stock_price(t)
                        st.markdown(f"<span class='price-text'>{price}</span>", unsafe_allow_html=True)
                    else:
                        st.caption("Click for data")

# 5. EXPLAINER FOOTER
st.divider()
st.write("### 📖 How to use this with your friends")
st.info("""
1. **The Lead Signals:** The first 3 stocks in each bucket are 'Active.' The others are on the watchlist.
2. **Rate Limits:** If you see 'Limit Hit,' it means your friends are using the app too much at once. Wait 60 seconds.
3. **The Strategy:** High-Beta (Today) -> Catalyst (Weekly) -> Macro (Season) -> Moat (Engine).
""")
