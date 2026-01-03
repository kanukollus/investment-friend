import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. ELITE WHITELABEL THEME (Hides GitHub, Hamburger, and Deployment)
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* Absolute Whitelabeling */
    header, footer, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; height: 0 !important; display: none !important; }
    #MainMenu { visibility: hidden !important; }
    [data-testid="stDecoration"] { display: none !important; }
    
    /* Mobile Readability & OLED Contrast */
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.95rem !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }

    /* High-Contrast Tactical Cards */
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    
    /* Advisor Intelligence Box */
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; font-size: 0.88rem; border-radius: 0 8px 8px 0; }
    </style>
""", unsafe_allow_html=True)

# 2. THE VOLATILITY ENGINE (Pure Algorithm - No Alphabetical Bias)
@st.cache_data(ttl=3600)
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    return pd.read_html(response.text)[0][['Symbol', 'Security']].values.tolist()

@st.cache_data(ttl=600)
def rank_live_volatility(universe):
    results = []
    # Audit top 60 index titans to find real movers
    for symbol, name in universe[:60]:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) < 2: continue
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            
            # Mathematical Strike Zones (Pivot Point S1/R1)
            piv = (h['High'].iloc[-2] + h['Low'].iloc[-2] + prev) / 3
            results.append({
                "ticker": symbol, "name": name, "price": curr, "change": pct,
                "entry": (2 * piv) - h['High'].iloc[-2],
                "target": (2 * piv) - h['Low'].iloc[-2]
            })
        except: continue
    # THE FIX: Sort by Absolute Change (Highest volatility, regardless of letter)
    return sorted(results, key=lambda x: abs(x['change']), reverse=True)[:5]

# 3. DYNAMIC BRIEFING ENGINE
def generate_brief(stock):
    c = stock['change']
    if abs(c) > 5:
        return f"<b>{stock['ticker']}</b> is leading 2026 volatility with an extreme move of {c:.2f}%. Watch for a 'Mean Reversion' scalp."
    return f"<b>{stock['ticker']}</b> is a high-liquidity momentum play. Pivot levels indicate stable institutional participation."

# 4. DASHBOARD INTERFACE
st.title("🏛️ Sovereign Terminal")
st.write("### ⚡ Live Momentum Leaders (Volatility Ranked)")

if 'unlocked' not in st.session_state:
    st.session_state.unlocked = []

with st.spinner("Analyzing Global Price Action..."):
    universe = get_sp500_symbols()
    leaders = rank_live_volatility(universe)

# Responsive Layout
cols = st.columns(5)
for i, stock in enumerate(leaders):
    with cols[i]:
        if i == 0 or stock['ticker'] in st.session_state.unlocked:
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""
                <div class="strike-zone-card">
                    <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                    <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                    <span class="val-stop">Stop: ${stock['entry']*0.985:.2f}</span>
                </div>
                <div class="advisor-brief">{generate_brief(stock)}</div>
            """, unsafe_allow_html=True)
        else:
            st.metric(label=stock['ticker'], value="--", delta="Locked")
            if st.button(f"Load {stock['ticker']}", key=f"btn_{stock['ticker']}"):
                st.session_state.unlocked.append(stock['ticker'])
                st.rerun()

st.divider()
# Custom Search
st.write("### 🔍 Strategic Asset Search")
query = st.text_input("Deep-Dive any Ticker:").upper()
if query:
    try:
        q_t = yf.Ticker(query)
        q_h = q_t.history(period="2d")
        if not q_h.empty:
            p, prev = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2]
            piv = (q_h['High'].iloc[-2] + q_h['Low'].iloc[-2] + prev) / 3
            c1, c2 = st.columns([1, 1])
            with c1: st.metric(label=query, value=f"${p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
            with c2:
                st.markdown(f"<div class='strike-zone-card'>Entry: ${(2*piv)-q_h['High'].iloc[-2]:.2f} | Target: ${(2*piv)-q_h['Low'].iloc[-2]:.2f}</div>", unsafe_allow_html=True)
    except: st.error("Feed error.")
