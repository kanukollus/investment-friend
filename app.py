import streamlit as st
import pandas as pd
import requests

# 1. THEME & FONT REFINEMENT
st.set_page_config(page_title="Advisor Terminal Pro", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    /* Professional Dark Theme Adjustments */
    .main { background-color: #0d1117; }
    .stMetric { border-radius: 8px; border: 1px solid #30363d; padding: 10px; background-color: #161b22; }
    
    /* Side-by-Side Align: Symbol + Button */
    .stock-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }
    .symbol-label { font-size: 1.1rem; font-weight: 600; color: #c9d1d9; width: 60px; }
    
    /* Clean Buttons */
    .stButton>button { height: 2.2em; border-radius: 6px; font-weight: 500; border: 1px solid #30363d; background: #21262d; color: #58a6ff; }
    .stButton>button:hover { border-color: #58a6ff; background: #30363d; }
    
    /* Status Pills */
    .pill { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
    .up { background-color: #23863622; color: #3fb950; border: 1px solid #238636; }
    .down { background-color: #da363322; color: #f85149; border: 1px solid #da3633; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE
API_KEY = "ZFVR5I30DHJS6MEV"

def get_advice_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE": return None
    try:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
        data = requests.get(url).json().get("Global Quote", {})
        if not data: return None
        return {
            "price": f"${float(data.get('05. price', 0)):,.2f}",
            "change": data.get("10. change percent", "0%"),
            "is_up": "-" not in data.get("10. change percent", "0")
        }
    except: return None

# 3. CURATED 2026 SELECTION
BUCKETS = {
    "⚡ TODAY": ["PLTR", "MU", "MRVL", "AMD", "RKLB"],
    "🗓️ WEEKLY": ["NVDA", "AVGO", "ANET", "WDC", "MSFT"],
    "🏗️ SEASONAL": ["VRT", "GEV", "OKLO", "PWR", "VST"],
    "🏦 ENGINE": ["TSM", "ASML", "AAPL", "AMZN", "KLAC"]
}

# 4. APP UI
st.title("🏛️ Senior Advisor Terminal")
st.markdown("<p style='color: #8b949e;'>Precision Investment Intelligence for 2026 Cycle</p>", unsafe_allow_html=True)

cols = st.columns(4)

for i, (bucket, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.write(f"#### {bucket}")
        st.divider()
        
        for t in tickers:
            # Layout Row
            r_col1, r_col2 = st.columns([1, 2])
            
            with r_col1:
                st.markdown(f"<div style='padding-top: 5px;'><span class='symbol-label'>{t}</span></div>", unsafe_allow_html=True)
            
            with r_col2:
                if st.button("Details", key=f"btn_{t}"):
                    data = get_advice_data(t)
                    if data:
                        status_class = "up" if data['is_up'] else "down"
                        st.markdown(f"""
                            <div class='pill {status_class}'>{data['price']} | {data['change']}</div>
                        """, unsafe_allow_html=True)
                    else:
                        st.caption("Feed Busy")
            st.write("") # Micro-spacing

# 5. THE "BUFFETT" FOOTER
st.divider()
st.subheader("Advisor's Strategy Focus")

st.write("""
In early 2026, the 'Easy AI money' has been made. We are now in the **Infrastructure Expansion** phase. 
Professional capital is moving from high-multiple software (SaaS) into the **Physical Constraints**: 
High-bandwidth networking and power generation for sovereign data centers.
""")
