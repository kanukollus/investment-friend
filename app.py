import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# 1. SETUP & THEMES
st.set_page_config(page_title="2026 Advisor Terminal", layout="wide")

# PLACE YOUR KEY HERE or use the 'demo' key to test (demo only works for IBM)
API_KEY = "ZFVR5I30DHJS6MEV" 

st.markdown("""
    <style>
    .metric-card { background-color: #161b22; border-radius: 10px; padding: 20px; border: 1px solid #30363d; }
    .status-live { color: #238636; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE (ALPHA VANTAGE)
@st.cache_data(ttl=600) # Refreshes every 10 mins
def fetch_alpha_data(ticker):
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
    r = requests.get(url)
    data = r.json()
    return data.get("Global Quote", {})

@st.cache_data(ttl=3600)
def fetch_alpha_history(ticker):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}'
    r = requests.get(url)
    data = r.json()
    # Convert JSON to DataFrame for Plotly
    ts = data.get("Time Series (Daily)", {})
    df = pd.DataFrame.from_dict(ts, orient='index').astype(float)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()

# 3. STRATEGY DEFINITIONS
STRATEGY = {
    "TODAY": {"ticker": "MU", "label": "Day Trade", "desc": "Memory Cycle Peak"},
    "WEEK": {"ticker": "NVDA", "label": "Swing", "desc": "AI Software Momentum"},
    "SEASON": {"ticker": "VRT", "label": "Tactical", "desc": "Power Grid Bottleneck"},
    "ENGINE": {"ticker": "TSM", "label": "Wealth", "desc": "Global Foundry Lead"}
}

# 4. APP UI
st.title("🏛️ Senior Advisor Terminal")
st.write(f"Connected to Private Data Feed | Stance: **Aggressive**")

if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE":
    st.warning("⚠️ Action Required: Please paste your Alpha Vantage API Key in the code to see live 2026 data.")

cols = st.columns(4)
for i, (horizon, info) in enumerate(STRATEGY.items()):
    with cols[i]:
        quote = fetch_alpha_data(info['ticker'])
        price = quote.get("05. price", "0.00")
        change = quote.get("10. change percent", "0.00%")
        
        st.markdown(f"### {horizon}")
        st.metric(label=f"{info['label']}: {info['ticker']}", value=f"${float(price):.2f}", delta=change)
        st.caption(info['desc'])
        
        if st.button(f"Analyze {info['ticker']}", key=f"btn_{i}"):
            st.session_state.active_ticker = info['ticker']

# 5. DEEP DIVE CHARTING
if 'active_ticker' in st.session_state:
    ticker = st.session_state.active_ticker
    st.divider()
    st.subheader(f"🔍 Strategic Analysis: {ticker}")
    
    df = fetch_alpha_history(ticker)
    if not df.empty:
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['1. open'], high=df['2. high'],
                        low=df['3. low'], close=df['4. close'])])
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    if st.button("Close Analysis"):
        del st.session_state.active_ticker
        st.rerun()
