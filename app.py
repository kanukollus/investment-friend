import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. PAGE CONFIG & THEME
st.set_page_config(page_title="2026 Sovereign AI Terminal", layout="wide")
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

# 2. DYNAMIC CONTENT GENERATOR (The "Reasoning" Engine)
def generate_dynamic_reasoning(ticker, change, price, name):
    """Generates a briefing based on data patterns rather than hardcoded text."""
    if change > 4:
        return f"<b>{name}</b> is currently the market's <b>Momentum Alpha</b>. With a {change:.2f}% surge, it has broken above the primary pivot, indicating aggressive institutional accumulation."
    elif change < -4:
        return f"<b>{name}</b> is undergoing a <b>Technical Flush</b>. The -{abs(change):.2f}% drop suggests high-volume profit taking. Monitor the Entry (S1) level for a mean-reversion scalp opportunity."
    elif abs(change) > 2:
        return f"<b>{name}</b> is showing <b>Elevated Volatility</b>. Institutional flow is currently { 'Bullish' if change > 0 else 'Bearish' }. This is a high-probability day trade setup."
    else:
        return f"<b>{name}</b> is showing <b>Stable Consolidation</b>. It has been selected due to its high liquidity and position within the top-movers of the S&P 500."

# 3. GLOBAL SCRAPER (Fetches S&P 500 dynamically)
@st.cache_data(ttl=3600)
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    # Added headers to look like a browser to prevent 403 blocks
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    df = pd.read_html(response.text)[0]
    return df[['Symbol', 'Security']].values.tolist()

@st.cache_data(ttl=600)
def fetch_top_movers(ticker_list):
    """Scans the top of the index to find the 5 most volatile stocks."""
    results = []
    # Scan the first 50 titans (largest by index weight) to stay within API limits
    for symbol, name in ticker_list[:50]:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) < 2: continue
            
            p_curr = hist['Close'].iloc[-1]
            p_prev = hist['Close'].iloc[-2]
            change = ((p_curr - p_prev) / p_prev) * 100
            
            # Pivot Math
            pivot = (hist['High'].iloc[-2] + hist['Low'].iloc[-2] + p_prev) / 3
            r1 = (2 * pivot) - hist['Low'].iloc[-2]
            s1 = (2 * pivot) - hist['High'].iloc[-2]
            
            results.append({
                "symbol": symbol, "name": name, "price": p_curr, "change": change,
                "entry": s1, "target": r1, "stop": s1 * 0.985, "over": p_curr > r1
            })
        except: continue
    # Dynamic Sort: Highest Absolute Change (The 'Active' Stocks)
    return sorted(results, key=lambda x: abs(x['change']), reverse=True)[:5]

# 4. DASHBOARD UI
st.title("🏛️ Sovereign Pure-Dynamic Terminal")
st.write("### ⚡ Today's Momentum Leaders (Algorithmic Selection)")

with st.spinner("Scraping S&P 500 and Ranking Volatility..."):
    sp500 = get_sp500_tickers()
    leaders = fetch_top_movers(sp500)

cols = st.columns(5)
for i, stock in enumerate(leaders):
    with cols[i]:
        status = "OVEREXTENDED" if stock['over'] else "STRIKE ZONE"
        p_color = "#f85149" if stock['over'] else "#3fb950"
        
        st.metric(label=stock['symbol'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
        
        # Tactical Box
        st.markdown(f"""
            <div class="strike-zone-card">
                <span style="color:{p_color}; font-size:0.7rem; font-weight:bold;">{status}</span><br>
                <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                <span class="val-stop">Stop: ${stock['stop']:.2f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Reasoning Box (Dynamic Reasoning)
        reasoning = generate_dynamic_reasoning(stock['symbol'], stock['change'], stock['price'], stock['name'])
        st.markdown(f"<div class='advisor-brief'>{reasoning}</div>", unsafe_allow_html=True)

st.divider()

# 5. UNIVERSAL SEARCH (Zero Constraints)
st.write("### 🔍 Strategic Asset Search")
query = st.text_input("Analyze any ticker in the world:").upper()
if query:
    try:
        q_ticker = yf.Ticker(query)
        q_h = q_ticker.history(period="2d")
        q_info = q_ticker.info
        if not q_h.empty:
            p = q_h['Close'].iloc[-1]
            prev = q_h['Close'].iloc[-2]
            c = ((p - prev) / prev) * 100
            piv = (q_h['High'].iloc[-2] + q_h['Low'].iloc[-2] + prev) / 3
            s1 = (2 * piv) - q_h['High'].iloc[-2]
            r1 = (2 * piv) - q_h['Low'].iloc[-2]
            
            c1, c2 = st.columns([1, 2])
            with c1: st.metric(label=query, value=f"${p:.2f}", delta=f"{c:.2f}%")
            with c2:
                st.markdown(f"""
                    <div class="strike-zone-card" style="font-size:1.1rem; padding:20px;">
                        <span class="val-entry">Entry: ${s1:.2f}</span> | 
                        <span class="val-target">Target: ${r1:.2f}</span> | 
                        <span class="val-stop">Stop: ${s1*0.985:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                res = generate_dynamic_reasoning(query, c, p, q_info.get('longName', query))
                st.markdown(f"<div class='advisor-brief'>{res}</div>", unsafe_allow_html=True)
    except:
        st.error("Ticker not found or data feed restricted.")
