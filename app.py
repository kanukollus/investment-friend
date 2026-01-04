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
    /* Absolute Whitelabel */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* Tactical Card Styling - NO NESTED DIVS TO PREVENT BREAKING */
    .card-container {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 15px;
    }
    .card-ticker { font-size: 1.5rem; font-weight: 800; color: #ffffff; }
    .card-name { font-size: 0.8rem; color: #8b949e; margin-bottom: 10px; display: block; }
    .card-price { font-size: 1.3rem; font-weight: 700; color: #ffffff; }
    
    .strike-zone-box { 
        background-color: #010409; 
        border: 1px solid #444c56; 
        padding: 10px; 
        border-radius: 8px; 
        margin-top: 10px; 
        font-family: monospace; 
        text-align: left; 
    }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. DYNAMIC AI HANDLER ---
def handle_ai_query(prompt, context, key):
    genai.configure(api_key=key)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        full_prompt = f"Context: {context}\n\nUser: {prompt}"
        time.sleep(1) # Basic throttle
        return model.generate_content(full_prompt).text
    except Exception as e:
        return f"⚠️ AI Service Busy. Please try in 30s."

# --- 4. DATA ENGINE (Back to High-Stability Core) ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    idx = 1 if "India" in exchange_choice else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers)
        df_list = pd.read_html(resp.text)
        symbols_df = df_list[idx]
        
        # Identity Mapping
        sym_col = 'Symbol'; name_col = 'Security' if idx == 0 else 'Company Name'
        names_map = dict(zip(symbols_df[sym_col], symbols_df[name_col]))
        raw_symbols = symbols_df[sym_col].tolist()
        
        if idx == 1: raw_symbols = [s + ".NS" for s in raw_symbols]
        
        sample = raw_symbols[::max(1, len(raw_symbols)//40)] 
        results = []
        for symbol in sample:
            try:
                t = yf.Ticker(symbol); h = t.history(period="5d")
                if len(h) < 2: continue
                curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                
                clean_sym = symbol.replace(".NS", "")
                results.append({
                    "ticker": symbol, "name": names_map.get(clean_sym, symbol), 
                    "price": curr, "change": ((curr-prev)/prev)*100,
                    "entry": (2*piv)-hi, "target": (2*piv)-lo, "abs_change": abs(((curr-prev)/prev)*100)
                })
            except: continue
        return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')
    except: return []

# --- 5. MAIN INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk", "📜 What is this app?"])

with tab_tactical:
    leaders = rank_movers(exchange_choice)
    curr_sym = "₹" if "India" in exchange_choice else "$"
    
    if not leaders:
        st.error("⚠️ Connection Error. The data provider is currently limiting requests. Please refresh in 60s.")
    else:
        leader_ctx = ""
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                color = "#3fb950" if stock['change'] >= 0 else "#f85149"
                st.markdown(f"""
                    <div class="card-container">
                        <div class="card-ticker">{stock['ticker']}</div>
                        <span class="card-name">{stock['name'][:20]}</span>
                        <div class="card-price">{curr_sym}{stock['price']:.2f}</div>
                        <div style="color:{color}; font-size:0.9rem; margin-bottom:10px;">
                            {'▲' if stock['change'] >= 0 else '▼'} {abs(stock['change']):.2f}%
                        </div>
                        <div class="strike-zone-box">
                            <span class="val-entry">Entry: {curr_sym}{stock['entry']:.2f}</span><br>
                            <span class="val-target">Target: {curr_sym}{stock['target']:.2f}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                leader_ctx += f"{stock['ticker']} ({curr_sym}{stock['price']:.2f}); "
        st.session_state.current_context = leader_ctx

    st.divider()
    search_q = st.text_input("Strategic Search (Ticker):").upper()
    if search_q:
        try:
            q_t = yf.Ticker(search_q); q_h = q_t.history(period="2d")
            p = q_h['Close'].iloc[-1]
            st.metric(label=search_q, value=f"{curr_sym}{p:.2f}")
        except: st.error("Search Feed Unavailable.")

with tab_research:
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear History"): st.session_state.messages = []; st.rerun()

    # RESTORED SUGGESTIONS
    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        suggestions = ["Analyze the leaders", "Define Strike Zone", "Trend Analysis"]
        s_cols = st.columns(3); clicked = None
        for idx, s in enumerate(suggestions):
            if s_cols[idx].button(s, use_container_width=True): clicked = s

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        prompt = st.chat_input("Ask about the tape...")
        final_query = prompt if prompt else clicked
        if final_query:
            st.session_state.messages.append({"role": "user", "content": final_query})
            with st.chat_message("user"): st.write(final_query)
            with st.chat_message("assistant"):
                ans = handle_ai_query(final_query, st.session_state.current_context, api_key)
                st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_about:
    st.markdown("""
    ### 🏛️ Sovereign Protocol (v40.0)
    * **Dynamic Discovery:** Real-time scrape of S&P 500 and Nifty 50.
    * **Volatility Ranking:** Magnified price movement sorting.
    * **Identity:** Security names displayed by default.
    * **Pivot Math:** Institutional Entry (S1) and Target (R1) levels.
    * **Multi-Currency:** Automatic symbol switching ($/₹).
    * **AI Desk:** Context-aware research with suggestion buttons.
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. <b>USER RESPONSIBILITY:</b> You are solely responsible for your financial decisions.</div>""", unsafe_allow_html=True)
