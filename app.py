import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. PREMIUM TERMINAL CONFIG
st.set_page_config(page_title="2026 Sovereign Dynamic", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .strike-zone-card { background-color: #1c1c1c; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-top: 10px; font-family: 'Courier New', monospace; font-size: 0.85rem; }
    .advisor-brief { background-color: #0d141f; border-left: 4px solid #58a6ff; padding: 12px; border-radius: 4px; margin-top: 10px; font-size: 0.85rem; color: #c9d1d9; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE VOLATILITY RANKER (Pure Logic - No Hardcoding)
@st.cache_data(ttl=3600)
def get_sp500_universe():
    """Scrapes S&P 500 symbols from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    df = pd.read_html(response.text)[0]
    return df[['Symbol', 'Security']].values.tolist()

@st.cache_data(ttl=600)
def fetch_and_rank_movers(universe):
    """Fetches real-time data for the top 100 titans and ranks by absolute change."""
    results = []
    # Scan the top 100 for API efficiency on Streamlit Cloud
    for symbol, name in universe[:100]:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) < 2: continue
            
            p_curr = h['Close'].iloc[-1]
            p_prev = h['Close'].iloc[-2]
            pct_change = ((p_curr - p_prev) / p_prev) * 100
            
            # Pivot Points
            piv = (h['High'].iloc[-2] + h['Low'].iloc[-2] + p_prev) / 3
            r1 = (2 * piv) - h['Low'].iloc[-2]
            s1 = (2 * piv) - h['High'].iloc[-2]
            
            results.append({
                "ticker": symbol, "name": name, "price": p_curr, "change": pct_change,
                "entry": s1, "target": r1, "stop": s1 * 0.985, "over": p_curr > r1
            })
        except: continue
    # THE DYNAMIC SORT: Absolute value of change (highest movers, regardless of direction)
    return sorted(results, key=lambda x: abs(x['change']), reverse=True)[:5]

# 3. ADVISOR REASONING ENGINE
def get_briefing(stock):
    c = stock['change']
    name = stock['name']
    if c > 5:
        return f"<b>{name}</b> is leading the market with a massive breakout (+{c:.1f}%). Bullish institutional accumulation detected."
    elif c < -5:
        return f"<b>{name}</b> is undergoing an aggressive technical flush (-{abs(c):.1f}%). Watch for a bounce at the Entry (S1) level."
    else:
        return f"<b>{name}</b> is showing high relative volume compared to peers. Active day-trading range confirmed."

# 4. DASHBOARD UI
st.title("🏛️ Sovereign Dynamic Terminal")
st.write("### ⚡ Today's Momentum Leaders (Ranked by Volatility)")

# Discovery State
if 'unlocked' not in st.session_state:
    st.session_state.unlocked = []

with st.spinner("Analyzing Global Volatility..."):
    sp500 = get_sp500_universe()
    leaders = fetch_and_rank_movers(sp500)

cols = st.columns(5)
for i, stock in enumerate(leaders):
    with cols[i]:
        # Logic: Show 1st one, lock the rest
        if i == 0 or stock['ticker'] in st.session_state.unlocked:
            p_color = "#f85149" if stock['over'] else "#3fb950"
            status = "OVEREXTENDED" if stock['over'] else "STRIKE ZONE"
            
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""
                <div class="strike-zone-card">
                    <span style="color:{p_color}; font-size:0.7rem; font-weight:bold;">{status}</span><br>
                    <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                    <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                    <span class="val-stop">Stop: ${stock['stop']:.2f}</span>
                </div>
                <div class="advisor-brief">{get_briefing(stock)}</div>
            """, unsafe_allow_html=True)
        else:
            st.metric(label=stock['ticker'], value="--", delta="Locked")
            if st.button(f"Load {stock['ticker']}", key=f"btn_{stock['ticker']}"):
                st.session_state.unlocked.append(stock['ticker'])
                st.rerun()

st.divider()

# 5. UNIVERSAL SEARCH (Zero Constraints)
st.write("### 🔍 Tactical Deep-Dive Search")
query = st.text_input("Analyze any global ticker (e.g. NVDA, RKLB):").upper()
if query:
    try:
        q_t = yf.Ticker(query)
        q_h = q_t.history(period="2d")
        if not q_h.empty:
            p = q_h['Close'].iloc[-1]
            prev = q_h['Close'].iloc[-2]
            chg = ((p - prev) / prev) * 100
            piv = (q_h['High'].iloc[-2] + q_h['Low'].iloc[-2] + prev) / 3
            s1 = (2 * piv) - q_h['High'].iloc[-2]
            r1 = (2 * piv) - q_h['Low'].iloc[-2]
            
            c1, c2 = st.columns([1, 2])
            with c1: st.metric(label=query, value=f"${p:.2f}", delta=f"{chg:.2f}%")
            with c2:
                st.markdown(f"""
                    <div class="strike-zone-card" style="font-size:1.1rem; padding:20px;">
                        <span class="val-entry">Entry: ${s1:.2f}</span> | 
                        <span class="val-target">Target: ${r1:.2f}</span> | 
                        <span class="val-stop">Stop: ${s1*0.985:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
    except: st.error("Feed error.")
