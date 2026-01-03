import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# 1. PAGE SETUP
st.set_page_config(page_title="2026 Advisor Terminal", layout="wide")
API_KEY = "ZFVR5I30DHJS6MEV"

# 2. PREMIUM CSS: The "Bloomberg" Aesthetic
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { width: 100%; border-radius: 4px; background-color: #21262d; border: 1px solid #30363d; color: #58a6ff; font-weight: 500; height: 2.2em; }
    .stButton>button:hover { border-color: #58a6ff; color: white; background-color: #30363d; }
    .symbol-text { font-family: 'Courier New', monospace; font-weight: bold; font-size: 1.1rem; color: #f0f6fc; }
    .advisor-brief { background: linear-gradient(90deg, #161b22 0%, #0d1117 100%); padding: 15px; border-left: 4px solid #238636; border-radius: 4px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# 3. ROBUST DATA ENGINE
@st.cache_data(ttl=600)
def fetch_advisor_data(ticker):
    if API_KEY == "YOUR_ALPHA_VANTAGE_KEY_HERE": return None
    try:
        # Quote Data
        q_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}'
        quote = requests.get(q_url).json().get("Global Quote", {})
        
        # History Data
        h_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}'
        hist_json = requests.get(h_url).json()
        ts_data = hist_json.get("Time Series (Daily)", {})
        
        if not ts_data: return None
        
        df = pd.DataFrame.from_dict(ts_data, orient='index').astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index() # Oldest to Newest
        
        return {
            "price": f"${float(quote.get('05. price', 0)):,.2f}",
            "change": quote.get("10. change percent", "0%"),
            "up": "-" not in quote.get("10. change percent", "0"),
            "df": df.last('30D') # Get last 30 days
        }
    except Exception: return None

# 4. ELITE 2026 BUCKETS
BUCKETS = {
    "⚡ TODAY": ["PLTR", "MU", "MRVL", "AMD", "RKLB"],
    "🗓️ WEEKLY": ["NVDA", "AVGO", "ANET", "WDC", "MSFT"],
    "🏗️ SEASONAL": ["VRT", "GEV", "OKLO", "PWR", "VST"],
    "🏦 ENGINE": ["GOOGL", "TSM", "ASML", "AAPL", "AMZN"]
}

# 5. UI CONSTRUCTION
st.title("🏛️ Senior Advisor Terminal")
st.markdown("<div class='advisor-brief'><b>System Briefing:</b> We are monitoring the 2026 'Agentic Cycle'. Infrastructure is cooling; Software integration is heating up.</div>", unsafe_allow_html=True)

cols = st.columns(4)
if 'active_ticker' not in st.session_state:
    st.session_state.active_ticker = None

for i, (name, tickers) in enumerate(BUCKETS.items()):
    with cols[i]:
        st.write(f"#### {name}")
        st.divider()
        for t in tickers:
            row_c1, row_c2 = st.columns([1, 1.5])
            with row_c1:
                st.markdown(f"<p style='margin-top:5px;'><span class='symbol-text'>{t}</span></p>", unsafe_allow_html=True)
            with row_c2:
                if st.button("Details", key=f"btn_{t}"):
                    st.session_state.active_ticker = t
            st.write("")

# 6. DYNAMIC DRILL-DOWN (The Bug-Free Graph)
if st.session_state.active_ticker:
    ticker = st.session_state.active_ticker
    st.divider()
    
    with st.spinner(f"Retrieving {ticker} Analytics..."):
        data = fetch_advisor_data(ticker)
    
    if data:
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.subheader(f"📈 {ticker} Momentum (30D)")
            # FIXED: We use .iloc[:, 3] which is ALWAYS the 4th column (Close)
            fig = go.Figure(data=[go.Scatter(x=data['df'].index, y=data['df'].iloc[:, 3], 
                            line=dict(color='#58a6ff', width=3), fill='tozeroy', fillcolor='rgba(88,166,255,0.1)')])
            fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,b=0,t=0),
                              xaxis_title="Date", yaxis_title="Price ($)")
            st.plotly_chart(fig, use_container_width=True)
            
        with c_right:
            clr = "#3fb950" if data['up'] else "#f85149"
            st.markdown(f"### Current: <span style='color:{clr}'>{data['price']}</span>", unsafe_allow_html=True)
            st.write(f"**Day Delta:** {data['change']}")
            st.markdown(f"**Advisor Verdict:** {ticker} is a core holding for the current 2026 macro-regime.")
            if st.button("Close Terminal"):
                st.session_state.active_ticker = None
                st.rerun()
    else:
        st.error(f"Data Feed for {ticker} is temporarily throttled. Please wait 60 seconds.")
