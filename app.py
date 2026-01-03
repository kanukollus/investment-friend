import streamlit as st
import pandas as pd
import requests

# 1. SETUP
st.set_page_config(page_title="Investment Friend 2026", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV" # <--- REPLACE WITH YOUR KEY

# 2. CUSTOM CSS FOR COLOR BOXES
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1f2428; color: #58a6ff; border: 1px solid #30363d; margin-bottom: 5px; }
    .stButton>button:hover { border-color: #58a6ff; }
    .price-box-up { background-color: #062512; padding: 10px; border-radius: 5px; border: 1px solid #238636; text-align: center; color: #3fb950; }
    .price-box-down { background-color: #2c1111; padding: 10px; border-radius: 5px; border: 1px solid #da3633; text-align: center; color: #f85149; }
    .advisor-note { font-style: italic; color: #8b949e; font-size: 0.9em; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. THE DATA ENGINE
def fetch_price_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE":
        return None
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        data = requests.get(url).json().get("Global Quote", {})
        if not data: return None
        return {
            "price": f"${float(data.get('05. price', 0)):,.2f}",
            "change": data.get("10. change percent", "0%"),
            "is_up": "-" not in data.get("10. change percent", "0")
        }
    except:
        return None

# 4. POWER 40 BUCKETS (2026 LEADERS)
BUCKETS = {
    "⚡ TODAY (Scalp)": ["MU", "AMD", "PLTR", "CIFR", "APLD", "SOFI", "RKLB", "MARA", "SMCI", "TSLA"],
    "🗓️ WEEKLY (Swing)": ["NVDA", "AVGO", "MSFT", "TTD", "META", "BULL", "ADBE", "SNOW", "CRWD", "TEAM"],
    "🏗️ SEASONAL (Macro)": ["VRT", "PWR", "GEV", "STRL", "EME", "MTZ", "J", "DY", "ENB", "COP"],
    "🏦 ENGINE (Wealth)": ["TSM", "ASML", "AAPL", "AMZN", "LRCX", "GOOGL", "KLAC", "ADI", "NEE", "CVX"]
}

# 5. DASHBOARD UI
st.title("🏛️ Senior Advisor Terminal")
st.write("Aggressive Default Stance: **Active** | Market: **Early 2026**")

cols = st.columns(4)

for i, (name, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.subheader(name)
        for t in tickers:
            if st.button(f"Analyze {t}", key=f"btn_{t}"):
                data = fetch_price_data(t)
                if data:
                    # Choose style based on 'is_up' boolean
                    box_class = "price-box-up" if data['is_up'] else "price-box-down"
                    st.markdown(f"""
                        <div class="{box_class}">
                            <b style="font-size: 1.3em;">{t}: {data['price']}</b><br>
                            <span>{data['change']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("API Limit Hit. Wait 60s.")
            else:
                st.write(f"• {t}")

# 6. ADVISOR LEGEND
st.divider()
st.info("💡 **Friend's Tip:** In 2026, the 'Physical AI' stocks (Power & Memory) are leading the Green moves. If you see a Red box in the ENGINE bucket, that's often a 'Buying Opportunity'.")
