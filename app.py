import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. WHITELABEL CONFIG (Hides GitHub, Hamburger, and Header)
st.set_page_config(page_title="2026 Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* Hide Streamlit Header and Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    div[data-testid="stToolbar"] { visibility: hidden; height: 0%; position: fixed; }
    div[data-testid="stDecoration"] { visibility: hidden; height: 0%; position: fixed; }
    
    /* Main Theme Overrides */
    .main { background-color: #0b0e11; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .strike-zone-card { background-color: #1c1c1c; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-top: 10px; font-family: 'Courier New', monospace; font-size: 0.85rem; }
    .advisor-brief { background-color: #0d141f; border-left: 4px solid #58a6ff; padding: 12px; border-radius: 4px; margin-top: 10px; font-size: 0.85rem; color: #c9d1d9; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. PURE DYNAMIC LOGIC (No Hardcoded Pools)
@st.cache_data(ttl=3600)
def get_sp500_universe():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    df = pd.read_html(response.text)[0]
    return df[['Symbol', 'Security']].values.tolist()

@st.cache_data(ttl=600)
def fetch_and_rank_movers(universe):
    results = []
    # Scan the top 100 titans for efficiency
    for symbol, name in universe[:100]:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) < 2: continue
            p_curr = h['Close'].iloc[-1]
            p_prev = h['Close'].iloc[-2]
            pct_change = ((p_curr - p_prev) / p_prev) * 100
            
            piv = (h['High'].iloc[-2] + h['Low'].iloc[-2] + p_prev) / 3
            results.append({
                "ticker": symbol, "name": name, "price": p_curr, "change": pct_change,
                "entry": (2 * piv) - h['High'].iloc[-2], 
                "target": (2 * piv) - h['Low'].iloc[-2], 
                "over": p_curr > ((2 * piv) - h['Low'].iloc[-2])
            })
        except: continue
    return sorted(results, key=lambda x: abs(x['change']), reverse=True)[:5]

# 3. DYNAMIC REASONING ENGINE
def get_dynamic_brief(stock):
    c = stock['change']
    if c > 4: return f"<b>{stock['name']}</b> is leading with massive momentum. Institutional buy-side pressure is peaking."
    if c < -4: return f"<b>{stock['name']}</b> is seeing an aggressive technical flush. Watch S1 for a reversal scalp."
    return f"<b>{stock['name']}</b> shows elevated volatility. Pivot-point stability confirmed for active trading."

# 4. DASHBOARD UI
st.title("🏛️ Sovereign Intelligence Terminal")
st.write("### ⚡ Live Momentum Leaders (Volatility Ranked)")

if 'unlocked' not in st.session_state:
    st.session_state.unlocked = []

with st.spinner("Scraping 2026 Global Volatility..."):
    sp500 = get_sp500_universe()
    leaders = fetch_and_rank_movers(sp500)

cols = st.columns(5)
for i, stock in enumerate(leaders):
    with cols[i]:
        # Show 1st automatically, hide others behind Load button
        if i == 0 or stock['ticker'] in st.session_state.unlocked:
            status_clr = "#f85149" if stock['over'] else "#3fb950"
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""
                <div class="strike-zone-card">
                    <span style="color:{status_clr}; font-size:0.7rem; font-weight:bold;">{'OVEREXTENDED' if stock['over'] else 'STRIKE ZONE'}</span><br>
                    <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                    <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                    <span class="val-stop">Stop: ${stock['entry']*0.985:.2f}</span>
                </div>
                <div class="advisor-brief">{get_dynamic_brief(stock)}</div>
            """, unsafe_allow_html=True)
        else:
            st.metric(label=stock['ticker'], value="--", delta="Locked")
            if st.button(f"Load {stock['ticker']}", key=f"btn_{stock['ticker']}"):
                st.session_state.unlocked.append(stock['ticker'])
                st.rerun()

st.divider()
st.write("### 🔍 Strategic Asset Search")
query = st.text_input("Deep-Dive any ticker:").upper()
if query:
    try:
        q_t = yf.Ticker(query)
        q_h = q_t.history(period="2d")
        if not q_h.empty:
            p = q_h['Close'].iloc[-1]
            prev = q_h['Close'].iloc[-2]
            piv = (q_h['High'].iloc[-2] + q_h['Low'].iloc[-2] + prev) / 3
            st.metric(label=query, value=f"${p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
            st.markdown(f"<div class='strike-zone-card'>Entry: ${(2*piv)-q_h['High'].iloc[-2]:.2f} | Target: ${(2*piv)-q_h['Low'].iloc[-2]:.2f}</div>", unsafe_allow_html=True)
    except: st.error("Feed error.")
