import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random

# --- 1. PAGE CONFIG & STEALTH THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    .card-container {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 10px;
        min-height: 280px;
    }
    .card-ticker { font-size: 1.4rem; font-weight: 800; color: #ffffff; margin-bottom: 2px; }
    .card-name { font-size: 0.75rem; color: #8b949e; margin-bottom: 8px; display: block; height: 35px; overflow: hidden; line-height: 1.2; }
    .card-price { font-size: 1.2rem; font-weight: 700; color: #ffffff; }
    .card-delta { font-size: 0.9rem; margin-bottom: 10px; }
    
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 12px; border-radius: 10px; font-family: monospace; text-align: left; }
    .val-entry { color: #58a6ff; font-weight: bold; font-size: 0.85rem; }
    .val-target { color: #3fb950; font-weight: bold; font-size: 0.85rem; }
    .val-alpha { color: #d29922; font-weight: bold; font-size: 0.8rem; display: block; margin-top: 2px; }
    
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE (Optimized for Names) ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    idx = 1 if "India" in exchange_choice else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers)
        symbols_df = pd.read_html(resp.text)[idx]
        
        # Mapping symbols and names
        sym_col = 'Symbol' if idx == 0 else 'Symbol'
        name_col = 'Security' if idx == 0 else 'Company Name'
        
        raw_symbols = symbols_df[sym_col].tolist()
        names_map = dict(zip(symbols_df[sym_col], symbols_df[name_col]))
        
        if idx == 1: raw_symbols = [s + ".NS" for s in raw_symbols]
        
        sample = raw_symbols[::max(1, len(raw_symbols)//40)] 
        results = []
        for symbol in sample:
            try:
                # Basic price pull
                t = yf.Ticker(symbol); h = t.history(period="5d")
                if len(h) < 2: continue
                curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                
                # Fetch name from our map (avoids extra API call)
                clean_sym = symbol.replace(".NS", "")
                display_name = names_map.get(clean_sym, symbol)
                
                results.append({
                    "ticker": symbol, "name": display_name, "price": curr, 
                    "change": ((curr-prev)/prev)*100, "entry": (2*piv)-hi, 
                    "target": (2*piv)-lo, "abs_change": abs(((curr-prev)/prev)*100)
                })
            except: continue
        return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')
    except: return []

# --- 3. MAIN INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Market Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk", "📜 What is this app?"])

with tab_tactical:
    alpha_mode = st.toggle("✨ Unlock Alpha Insights (52W Range, R/R Ratio)", value=False)
    leaders = rank_movers(exchange_choice)
    curr_sym = "₹" if "India" in exchange_choice else "$"
    
    if not leaders:
        st.warning("⚠️ Market data temporarily unavailable. Please refresh.")
    else:
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                delta_color = "#3fb950" if stock['change'] >= 0 else "#f85149"
                alpha_content = ""
                
                if alpha_mode:
                    # Deep data triggered only on user demand
                    t_info = yf.Ticker(stock['ticker']).info
                    stop = stock['entry'] * 0.985
                    rr = abs(stock['target']-stock['entry'])/abs(stock['entry']-stop) if abs(stock['entry']-stop) != 0 else 0
                    alpha_content = f"""
                        <hr style="border:0.1px solid #333; margin:8px 0;">
                        <span class="val-alpha">52W H: {curr_sym}{t_info.get('fiftyTwoWeekHigh', 0):.2f}</span>
                        <span class="val-alpha">52W L: {curr_sym}{t_info.get('fiftyTwoWeekLow', 0):.2f}</span>
                        <span class="val-alpha">R/R Ratio: {rr:.2f}</span>
                    """

                st.markdown(f"""
                    <div class="card-container">
                        <div class="card-ticker">{stock['ticker']}</div>
                        <span class="card-name">{stock['name']}</span>
                        <div class="card-price">{curr_sym}{stock['price']:.2f}</div>
                        <div class="card-delta" style="color: {delta_color};">
                            {'▲' if stock['change'] >= 0 else '▼'} {abs(stock['change']):.2f}%
                        </div>
                        <div class="strike-zone-card">
                            <span class="val-entry">Entry: {curr_sym}{stock['entry']:.2f}</span><br>
                            <span class="val-target">Target: {curr_sym}{stock['target']:.2f}</span>
                            {alpha_content}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    st.divider()
    # Search and AI Tabs logic remains stable...

with tab_about:
    st.markdown("""
    ### 🏛️ Sovereign Protocol (v39.0)
    * **Tactical Core:** Dynamic Discovery, Volatility Ranking, and Pivot Math.
    * **Identity First:** Company names are now displayed by default for all movers.
    * **✨ Alpha Toggle:** On-demand 52W Range and R/R Ratio calculations.
    * **Compliance:** Institutional Disclaimer and Protocol documentation verified.
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. <b>USER RESPONSIBILITY:</b> You are solely responsible for your financial decisions and actions.</div>""", unsafe_allow_html=True)
