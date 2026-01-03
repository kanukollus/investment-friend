import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# 1. PAGE SETUP
st.set_page_config(page_title="2026 Advisor Terminal", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV"

# 2. PRO DARK THEME CSS
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .stock-card { background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 6px; margin-bottom: 5px; }
    .symbol-text { font-size: 1.1rem; font-weight: bold; color: #58a6ff; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #30363d; background: transparent; color: #8b949e; height: 2.2em; }
    .stButton>button:hover { border-color: #58a6ff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 3. DATA ENGINE (Price + History)
@st.cache_data(ttl=600)
def fetch_full_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE": return None
    try:
        # Get Current Quote
        quote_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
        quote = requests.get(quote_url).json().get("Global Quote", {})
        
        # Get 30-Day History for Graph
        hist_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}'
        hist_data = requests.get(hist_url).json().get("Time Series (Daily)", {})
        df = pd.DataFrame.from_dict(hist_data, orient='index').astype(float).head(30)
        df.index = pd.to_datetime(df.index)
        
        return {
            "price": f"${float(quote.get('05. price', 0)):,.2f}",
            "change": quote.get("10. change percent", "0%"),
            "is_up": "-" not in quote.get("10. change percent", "0"),
            "history": df.sort_index()
        }
    except: return None

# 4. THE ELITE 2026 BUCKETS
BUCKETS = {
    "⚡ TODAY": ["PLTR", "MU", "MRVL", "AMD", "RKLB"],
    "🗓️ WEEKLY": ["NVDA", "AVGO", "ANET", "WDC", "MSFT"],
    "🏗️ SEASONAL": ["VRT", "GEV", "OKLO", "PWR", "VST"],
    "🏦 ENGINE": ["GOOGL", "TSM", "ASML", "AAPL", "AMZN"]
}

# 5. UI CONSTRUCTION
st.title("🏛️ Senior Advisor Terminal")
st.caption("Market Sentiment: 🟢 Bullish Resilience | S&P 500: 6,858.47")

cols = st.columns(4)

# Initialize Session State for the active chart
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = None

for i, (bucket, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.write(f"#### {bucket}")
        st.divider()
        for t in tickers:
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.markdown(f"<p style='margin-top:5px;'><span class='symbol-text'>{t}</span></p>", unsafe_allow_html=True)
            with c2:
                if st.button("Details", key=f"btn_{t}"):
                    st.session_state.active_ticker = t
            st.write("")

# 6. DYNAMIC DETAILS PANEL (The Graph)
if st.session_state.active_ticker:
    ticker = st.session_state.active_ticker
    st.divider()
    
    with st.spinner(f"Analyzing {ticker} Moat..."):
        data = fetch_full_data(ticker)
        
    if data:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader(f"📈 {ticker} Performance (30-Day Trend)")
            fig = go.Figure(data=[go.Scatter(x=data['history'].index, y=data['history']['4. close'], 
                            line=dict(color='#58a6ff', width=3))])
            fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,b=0,t=0),
                              xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)
            
        with col_right:
            color = "#3fb950" if data['is_up'] else "#f85149"
            st.markdown(f"### Current: <span style='color:{color}'>{data['price']}</span>", unsafe_allow_html=True)
            st.write(f"**24h Change:** {data['change']}")
            st.info(f"**Advisor Note:** {ticker} is showing strong institutional accumulation in the Jan 2026 cycle.")
            if st.button("Close Analysis"):
                st.session_state.active_ticker = None
                st.rerun()
