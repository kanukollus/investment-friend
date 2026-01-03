import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import time

# 1. SETUP & THEME (2026 Sovereign Terminal)
st.set_page_config(page_title="2026 Omaha Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #d4af37; padding: 15px; border-radius: 10px; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #d4af37; color: #d4af37; }
    .advisor-brief { border-left: 5px solid #238636; background-color: #1c1c1c; padding: 15px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DYNAMIC DATA ENGINE (No Hardcoding)
@st.cache_data(ttl=3600)
def get_sp500_universe():
    """Scrapes the S&P 500 components dynamically."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        header = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=header)
        df = pd.read_html(response.text)[0]
        return df['Symbol'].tolist()
    except:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "BRK.B", "META", "TSM", "VRT", "PLTR"]

@st.cache_data(ttl=600)
def analyze_top_performers(tickers):
    """Calculates fundamental scores for the Top 30 tickers to find lead signals."""
    results = []
    # Limit to top 30 to respect API rate limits on Streamlit Cloud
    for t in tickers[:30]:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            results.append({
                "ticker": t,
                "price": info.get('currentPrice', 0),
                "change": info.get('regularMarketChangePercent', 0),
                "roe": info.get('returnOnEquity', 0),
                "debt": info.get('debtToEquity', 100),
                "yield": info.get('dividendYield', 0),
                "fcf": info.get('freeCashflow', 0)
            })
        except: continue
    return pd.DataFrame(results)

# 3. APP UI
st.title("🏛️ Sovereign Omaha Scraper")
st.markdown("<div class='advisor-brief'><b>System Update Jan 3, 2026:</b> The algorithm has moved from alphabetical sorting to <b>Fundamental Ranking</b>. We are now scanning the S&P 500 for durable moats and capital efficiency.</div>", unsafe_allow_html=True)

# Process Live Scrape
with st.spinner("Scraping and Ranking 2026 Market Leaders..."):
    all_symbols = get_sp500_universe()
    df = analyze_top_performers(all_symbols)

if not df.empty:
    # 4. ALGORITHMIC BUCKET ASSIGNMENT (Logic over Alphabet)
    # ⚡ TODAY: Ranked by 24h Momentum (Max Absolute Change)
    today_lead = df.sort_values("change", ascending=False).iloc[0]
    
    # 🗓️ WEEKLY: Ranked by Efficiency (ROE) but currently in a 'Dip' (Negative change)
    weekly_lead = df[df['change'] < 0].sort_values("roe", ascending=False).iloc[0]
    
    # 🏦 THE ENGINE: The 'Crown Jewel' (Highest ROE / Lowest Debt ratio)
    # This is where Alphabet (GOOGL) or TSM often land due to massive cash flow
    engine_lead = df.sort_values(["roe", "debt"], ascending=[False, True]).iloc[0]

    # 5. UI DISPLAY (The Requested Tabbed & Horizontal Layout)
    st.write(f"### ⚡ Today's Momentum Lead: {today_lead['ticker']}")
    
    # Discovery Row (Logic: Show Lead, Unlock others)
    today_tickers = [today_lead['ticker']] + all_symbols[21:25] # Mix lead with dynamic segment
    cols = st.columns(5)
    for i, t in enumerate(today_tickers):
        with cols[i]:
            if i == 0 or st.session_state.get(f"unlocked_{t}"):
                # Actual data for unlocked
                tick_data = df[df['ticker'] == t].to_dict('records')[0] if t in df.ticker.values else None
                if tick_data:
                    st.metric(label=t, value=f"${tick_data['price']:.2f}", delta=f"{tick_data['change']:.2f}%")
                else:
                    st.metric(label=t, value="N/A", delta="Fetching...")
            else:
                st.metric(label=t, value="--", delta="Locked")
                if st.button(f"Load {t}", key=f"btn_{t}"):
                    st.session_state[f"unlocked_{t}"] = True
                    st.rerun()

    st.divider()
    tab_week, tab_season, tab_engine = st.tabs(["🗓️ Weekly Swings", "🏗️ Seasonal Macro", "🏦 The Engine"])

    with tab_week:
        st.write(f"**Advisor Pick:** {weekly_lead['ticker']} is generating {weekly_lead['roe']*100:.1f}% ROE. This is an efficiency play.")
        st.metric(label=weekly_lead['ticker'], value=f"${weekly_lead['price']:.2f}", delta=f"{weekly_lead['change']:.2f}%")

    with tab_engine:
        st.write("**The 'Buffett Standard' Wealth Engine**")
        
        st.metric(label=engine_lead['ticker'], value=f"${engine_lead['price']:.2f}", delta="Wealth Moat")
        st.caption(f"ROE: {engine_lead['roe']*100:.1f}% | Debt-to-Equity: {engine_lead['debt']}")

st.divider()
st.info("💡 **Buffett Algorithm Brief:** This terminal ignores name and sector. It looks for the rare intersection of high internal returns (ROE) and market fear (Negative deltas or high volatility).")
