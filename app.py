import streamlit as st
import pandas as pd
import yfinance as yf

# 1. PREMIUM TERMINAL CONFIG
st.set_page_config(page_title="2026 Live Strike Zone", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .strike-zone-card { background-color: #1c1c1c; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-top: 10px; font-family: 'Courier New', monospace; font-size: 0.85rem; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    .status-pill { padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: bold; display: inline-block; margin-bottom: 5px; }
    .pill-red { background-color: #da363322; color: #f85149; border: 1px solid #da3633; }
    .pill-green { background-color: #23863622; color: #3fb950; border: 1px solid #238636; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE DYNAMIC SCANNER (The "Brain")
@st.cache_data(ttl=600)
def get_dynamic_momentum_leaders():
    # A broad pool of 2026 high-volume stocks to scan
    pool = ["NVDA", "TSLA", "PLTR", "MU", "AMD", "META", "AVGO", "MSFT", "AAPL", "GOOGL", "AMZN", "RKLB", "CIFR", "APLD", "SOFI"]
    data = []
    for t in pool:
        try:
            s = yf.Ticker(t)
            h = s.history(period="2d")
            change = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
            data.append({"ticker": t, "abs_change": abs(change), "change": change, "hist": h})
        except: continue
    
    # Sort by absolute change (highest volatility) and pick Top 5
    df = pd.DataFrame(data).sort_values(by="abs_change", ascending=False)
    return df.head(5).to_dict('records')

# 3. THE STRIKE ZONE LOGIC
def calculate_levels(hist):
    prev = hist.iloc[-2]
    curr = hist.iloc[-1]
    pivot = (prev['High'] + prev['Low'] + prev['Close']) / 3
    r1 = (2 * pivot) - prev['Low']
    s1 = (2 * pivot) - prev['High']
    is_over = curr['Close'] > r1
    return {
        "price": curr['Close'],
        "entry": s1,
        "target": r1,
        "stop": s1 * 0.985,
        "status": "OVEREXTENDED" if is_over else "STRIKE ZONE",
        "pill": "pill-red" if is_over else "pill-green"
    }

# 4. DASHBOARD UI
st.title("🎯 Sovereign Strike Zone Pro: Dynamic")
st.write("### ⚡ Live Momentum Leaders (Sorted by Volatility)")

with st.spinner("Scanning 2026 Market Liquidity..."):
    leaders = get_dynamic_momentum_leaders()

cols = st.columns(5)
for i, stock in enumerate(leaders):
    with cols[i]:
        setup = calculate_levels(stock['hist'])
        st.metric(label=stock['ticker'], value=f"${setup['price']:.2f}", delta=f"{stock['change']:.2f}%")
        st.markdown(f"""
            <div class="strike-zone-card">
                <div class="status-pill {setup['pill']}">{setup['status']}</div><br>
                <span class="val-entry">Entry: ${setup['entry']:.2f}</span><br>
                <span class="val-target">Target: ${setup['target']:.2f}</span><br>
                <span class="val-stop">Stop: ${setup['stop']:.2f}</span>
            </div>
        """, unsafe_allow_html=True)

st.divider()
st.write("### 🔍 Custom Tactical Search")
query = st.text_input("Enter any ticker for deep-dive analysis:").upper()
if query:
    q_stock = yf.Ticker(query)
    q_hist = q_stock.history(period="2d")
    if not q_hist.empty:
        q_setup = calculate_levels(q_hist)
        c1, c2 = st.columns([1, 2])
        with c1: st.metric(label=query, value=f"${q_setup['price']:.2f}")
        with c2:
            st.markdown(f"""<div class="strike-zone-card" style="font-size: 1.1rem; padding: 20px;">
                <div class="status-pill {q_setup['pill']}">{q_setup['status']}</div><br>
                <span class="val-entry">Entry: ${q_setup['entry']:.2f}</span> | 
                <span class="val-target">Target: ${q_setup['target']:.2f}</span> | 
                <span class="val-stop">Stop: ${q_setup['stop']:.2f}</span></div>""", unsafe_allow_html=True)
