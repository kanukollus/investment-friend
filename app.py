import streamlit as st
import requests

# 1. SETUP
st.set_page_config(page_title="2026 Advisor Terminal", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV" 

# 2. ENHANCED CSS
st.markdown("""
    <style>
    /* Align buttons and text vertically center */
    [data-testid="column"] { display: flex; align-items: center; }
    .stButton>button { width: 100%; border-radius: 4px; height: 2.5em; background-color: #1f2428; color: #58a6ff; border: 1px solid #30363d; margin-top: 0px; }
    .price-box-up { background-color: #062512; padding: 8px; border-radius: 4px; border: 1px solid #238636; text-align: center; color: #3fb950; width: 100%; margin-top: 5px; }
    .price-box-down { background-color: #2c1111; padding: 8px; border-radius: 4px; border: 1px solid #da3633; text-align: center; color: #f85149; width: 100%; margin-top: 5px; }
    .symbol-text { font-weight: bold; font-size: 1.1em; color: white; margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. DATA ENGINE
def fetch_price_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE": return None
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    try:
        data = requests.get(url).json().get("Global Quote", {})
        if not data: return None
        return {
            "price": f"${float(data.get('05. price', 0)):,.2f}",
            "change": data.get("10. change percent", "0%"),
            "is_up": "-" not in data.get("10. change percent", "0")
        }
    except: return None

# 4. 2026 SECOND-WAVE BUCKETS
BUCKETS = {
    "⚡ TODAY (Networking)": ["MRVL", "ANET", "ALAB", "CRDO", "FN", "AVGO", "MU", "PLTR", "AMD", "TSLA"],
    "🗓️ WEEKLY (Storage)": ["WDC", "STX", "PSTG", "NTAP", "SNOW", "MSFT", "META", "AMZN", "GOOGL", "BULL"],
    "🏗️ SEASONAL (Power)": ["VRT", "PWR", "GEV", "NEE", "CEG", "VST", "OKLO", "SMR", "ENB", "COP"],
    "🏦 ENGINE (Foundry)": ["TSM", "ASML", "KLAC", "LRCX", "AMAT", "AAPL", "ADI", "TXN", "INTC", "ARM"]
}

# 5. UI
st.title("🏛️ Senior Advisor Terminal")
st.markdown(f"""<div style='background-color: #1f2428; border-left: 5px solid #58a6ff; padding: 15px; border-radius: 8px;'>
    <b>Jan 3, 2026 Briefing:</b> The S&P 500 is testing 6,900. While GPUs remain stable, the real action is in <b>1.6T Networking</b> (MRVL, ANET) 
    and <b>High-Density Storage</b> (WDC) as the world pivots to 'Agentic AI'.
    </div>""", unsafe_allow_html=True)

st.write("") # Spacer

cols = st.columns(4)

for i, (name, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.subheader(name)
        st.divider()
        for t in tickers:
            # Layout: Symbol (Left) and Button (Right)
            row_col1, row_col2 = st.columns([1, 2])
            
            with row_col1:
                st.markdown(f"<p class='symbol-text'>{t}</p>", unsafe_allow_html=True)
            
            with row_col2:
                if st.button("Analyze", key=f"btn_{t}"):
                    data = fetch_price_data(t)
                    if data:
                        box_class = "price-box-up" if data['is_up'] else "price-box-down"
                        st.markdown(f"""
                            <div class="{box_class}">
                                <b>{data['price']}</b><br><small>{data['change']}</small>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Limit Hit")
            st.write("") # Minor vertical spacing between rows

st.divider()
st.info("💡 **Friend's Tip:** Notice the 'TODAY' bucket has shifted to Networking providers like Marvell (MRVL). They are currently the 'Cisco of 2026'.")
