import streamlit as st
import pandas as pd
import requests

# 1. THEME: "The Omaha Terminal"
st.set_page_config(page_title="2026 Advisor Terminal", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    .main { background-color: #0d1111; }
    /* Modern Row Styling */
    .stock-row { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 12px; 
        border-bottom: 1px solid #30363d;
        background-color: #161b22;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .symbol { font-weight: 700; font-size: 1.1rem; color: #58a6ff; }
    /* Pill Styling for Price */
    .pill-up { background-color: #238636; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.85rem; }
    .pill-down { background-color: #da3633; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.85rem; }
    .stButton>button { border-radius: 20px; border: 1px solid #30363d; background: transparent; color: #8b949e; height: 2.2em; font-size: 0.8rem; }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE
API_KEY = "ZFVR5I30DHJS6MEV"

def fetch_pro_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE": return None
    try:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
        data = requests.get(url).json().get("Global Quote", {})
        if not data: return None
        return {
            "price": f"${float(data.get('05. price', 0)):,.2f}",
            "change": data.get("10. change percent", "0%"),
            "up": "-" not in data.get("10. change percent", "0")
        }
    except: return None

# 3. THE ELITE 20 (Refined for Jan 2026)
BUCKETS = {
    "⚡ TODAY": ["PLTR", "MU", "MRVL", "AMD", "RKLB"],
    "🗓️ WEEKLY": ["NVDA", "AVGO", "ANET", "WDC", "MSFT"],
    "🏗️ SEASONAL": ["VRT", "GEV", "OKLO", "PWR", "VST"],
    "🏦 ENGINE": ["GOOGL", "TSM", "ASML", "AAPL", "AMZN"] # Alphabet Added Here
}

# 4. DASHBOARD HEADER
st.title("🏛️ Senior Advisor Terminal")
st.markdown("<p style='color: #8b949e; margin-bottom: 30px;'>January 2026 | Cycle: Infrastructure Inflection</p>", unsafe_allow_html=True)

# 5. UI CONSTRUCTION
cols = st.columns(4)

for i, (bucket, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.markdown(f"#### {bucket}")
        st.write("") 
        
        for t in tickers:
            # Create the Side-by-Side Row
            with st.container():
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    st.markdown(f"<p style='margin-top: 5px;'><span class='symbol'>{t}</span></p>", unsafe_allow_html=True)
                with c2:
                    if st.button("Details", key=f"btn_{t}"):
                        data = fetch_pro_data(t)
                        if data:
                            p_class = "pill-up" if data['up'] else "pill-down"
                            st.markdown(f"<span class='{p_class}'>{data['price']} | {data['change']}</span>", unsafe_allow_html=True)
                        else:
                            st.caption("Feed Busy")
            st.markdown("<hr style='margin: 8px 0; border-color: #30363d;'>", unsafe_allow_html=True)

# 6. ADVISOR'S FINAL WORD
st.divider()
st.write("### 🏛️ Why Alphabet (GOOGL) is in the Engine")
st.write("""
In 2026, **Alphabet** has moved from a 'Search Company' to the world's most efficient **AI Vertically Integrated Utility**. 
By owning the chips (TPUs), the data (Search/YouTube), and the agentic interface (Gemini), they possess a cost-per-inference 
advantage that competitors cannot match. It is a 'Forever' stock for the Engine bucket.
""")
