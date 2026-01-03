import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. WHITELABEL & HIGH-CONTRAST MOBILE THEME
st.set_page_config(page_title="2026 Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* HIDE TOP NAV & BRANDING */
    header, footer, [data-testid="stToolbar"], .stDeployButton { visibility: hidden !important; height: 0 !important; }
    #MainMenu { visibility: hidden !important; }
    
    /* MOBILE FONT & BACKGROUND */
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* METRIC CARDS - HIGH CONTRAST */
    [data-testid="stMetric"] {
        background-color: #161b22; 
        border: 1px solid #30363d; 
        padding: 1rem !important;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.95rem !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }

    /* STRIKE ZONE CARDS */
    .strike-zone-card {
        background-color: #010409;
        border: 1px solid #444c56;
        padding: 14px;
        border-radius: 10px;
        margin-top: 10px;
        font-family: 'Courier New', Courier, monospace;
    }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    
    /* ADVISOR BRIEF */
    .advisor-brief {
        background-color: #161b22;
        border-left: 4px solid #d29922;
        color: #e6edf3;
        padding: 12px;
        margin-top: 8px;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
    }
    </style>
""", unsafe_allow_html=True)

# 2. THE PURE DYNAMIC ENGINE (No Hardcoding)
@st.cache_data(ttl=3600)
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    df = pd.read_html(response.text)[0]
    return df[['Symbol', 'Security']].values.tolist()

@st.cache_data(ttl=600)
def fetch_top_volatility_leaders(universe):
    results = []
    for symbol, name in universe[:60]: # Scan top 60 titans
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) < 2: continue
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            piv = (h['High'].iloc[-2] + h['Low'].iloc[-2] + prev) / 3
            results.append({
                "ticker": symbol, "name": name, "price": curr, "change": pct,
                "entry": (2 * piv) - h['High'].iloc[-2],
                "target": (2 * piv) - h['Low'].iloc[-2]
            })
        except: continue
    return sorted(results, key=lambda x: abs(x['change']), reverse=True)[:5]

# 3. DYNAMIC REASONING ENGINE
def get_brief(stock):
    c = stock['change']
    if c > 4: return f"<b>{stock['ticker']}</b> is leading with high-velocity breakout momentum. Watch the target for profit capture."
    if c < -4: return f"<b>{stock['ticker']}</b> is undergoing a technical flush. Monitor the entry level for a reversal scalp."
    return f"<b>{stock['ticker']}</b> shows elevated volatility. Pivot-point stability is confirmed for day-trading."

# 4. DASHBOARD INTERFACE
st.title("🏛️ Sovereign Terminal")
st.write("### ⚡ Live Momentum Leaders")

if 'unlocked' not in st.session_state:
    st.session_state.unlocked = []

with st.spinner("Scraping Global Markets..."):
    universe = get_sp500_symbols()
    leaders = fetch_top_volatility_leaders(universe)

# Display Top 5 in a responsive row
cols = st.columns(5)
for i, stock in enumerate(leaders):
    with cols[i]:
        # Logic: 1st is visible, others require 'Load'
        if i == 0 or stock['ticker'] in st.session_state.unlocked:
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            
            st.markdown(f"""
                <div class="strike-zone-card">
                    <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                    <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                    <span class="val-stop">Stop: ${stock['entry']*0.985:.2f}</span>
                </div>
                <div class="advisor-brief">{get_brief(stock)}</div>
            """, unsafe_allow_html=True)
        else:
            st.metric(label=stock['ticker'], value="--", delta="Locked")
            if st.button(f"Load {stock['ticker']}", key=f"btn_{stock['ticker']}"):
                st.session_state.unlocked.append(stock['ticker'])
                st.rerun()

st.divider()

# 5. UNIVERSAL SEARCH ENGINE
st.write("### 🔍 Strategic Asset Search")
query = st.text_input("Deep-Dive any ticker (e.g., NVDA, RKLB):").upper()
if query:
    try:
        q_t = yf.Ticker(query)
        q_h = q_t.history(period="2d")
        if not q_h.empty:
            p = q_h['Close'].iloc[-1]
            prev = q_h['Close'].iloc[-2]
            piv = (q_h['High'].iloc[-2] + q_h['Low'].iloc[-2] + prev) / 3
            e, t = (2*piv)-q_h['High'].iloc[-2], (2*piv)-q_h['Low'].iloc[-2]
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.metric(label=query, value=f"${p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
            with c2:
                st.markdown(f"""
                    <div class="strike-zone-card">
                        <span class="val-entry">Entry: ${e:.2f}</span><br>
                        <span class="val-target">Target: ${t:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
    except:
        st.error("Feed connection error.")
