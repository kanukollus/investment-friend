import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 1. Terminal Configuration
st.set_page_config(page_title="Buffett Dynamic Scraper", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #d4af37; padding: 20px; border-radius: 12px; }
    .advisor-brief { border-left: 5px solid #238636; background-color: #1c1c1c; padding: 15px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE DYNAMIC SCRAPER (No Hardcoding)
@st.cache_data(ttl=86400) # Only scrape once a day
def get_sp500_tickers():
    # Dynamically pull S&P 500 constituents from Wikipedia
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    return df['Symbol'].tolist()

@st.cache_data(ttl=3600)
def analyze_universe(ticker_list):
    results = []
    # Limit to Top 30 to prevent API throttling
    scan_list = ticker_list[:30] 
    
    progress_bar = st.progress(0)
    for i, t in enumerate(scan_list):
        try:
            stock = yf.Ticker(t)
            info = stock.info
            
            # Buffett Metrics: Return on Equity, Debt, and Price Delta
            results.append({
                "ticker": t,
                "price": info.get('currentPrice', 0),
                "roe": info.get('returnOnEquity', 0),
                "debt": info.get('debtToEquity', 100),
                "yield": info.get('dividendYield', 0),
                "change": info.get('regularMarketChangePercent', 0)
            })
            progress_bar.progress((i + 1) / len(scan_list))
        except: continue
    return pd.DataFrame(results)

# 3. THE INTERFACE
st.title("🏛️ Sovereign Omaha Scraper")
st.markdown("<div class='advisor-brief'><b>System Note:</b> No hardcoded universe detected. Scraping Wikipedia for the current S&P 500 components...</div>", unsafe_allow_html=True)

# Process Data
tickers = get_sp500_tickers()
df = analyze_universe(tickers)

if not df.empty:
    # ALGORITHMIC ASSIGNMENT
    # ⚡ TODAY: Highest 24h Volatility (for scalps)
    today_pick = df.sort_values("change", ascending=False).iloc[0]
    
    # 🗓️ WEEKLY: High ROE but currently down (value swing)
    weekly_pick = df[df['change'] < 0].sort_values("roe", ascending=False).iloc[0]
    
    # 🏗️ SEASONAL: High Yield & Stable Debt
    seasonal_pick = df.sort_values("yield", ascending=False).iloc[0]
    
    # 🏦 ENGINE: The ultimate "Moat" (Max ROE, Min Debt)
    engine_pick = df.sort_values(["roe", "debt"], ascending=[False, True]).iloc[0]

    cols = st.columns(4)
    with cols[0]:
        st.subheader("⚡ TODAY")
        st.metric(label=today_pick['ticker'], value=f"${today_pick['price']:.2f}", delta=f"{today_pick['change']:.2f}%")
        st.caption("Momentum Leader")

    with cols[1]:
        st.subheader("🗓️ WEEKLY")
        st.metric(label=weekly_pick['ticker'], value=f"${weekly_pick['price']:.2f}", delta=f"{weekly_pick['change']:.2f}%")
        st.caption("Efficiency at a Discount")

    with cols[2]:
        st.subheader("🏗️ SEASONAL")
        st.metric(label=seasonal_pick['ticker'], value=f"${seasonal_pick['price']:.2f}", delta=f"{seasonal_pick['change']:.2f}%")
        st.caption("Dividend Engine")

    with cols[3]:
        st.subheader("🏦 ENGINE")
        st.metric(label=engine_pick['ticker'], value=f"${engine_pick['price']:.2f}", delta=f"{engine_pick['change']:.2f}%")
        st.caption("High-Moat Champion")

st.divider()
st.write("### The Buffett Decision Framework")

st.info("This algorithm prioritizes **Return on Equity (ROE)**. In Buffett's view, a company that can generate 20%+ ROE without taking on massive debt is a 'Wonderful Company' at a fair price.")
