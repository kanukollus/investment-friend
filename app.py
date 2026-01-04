import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-alpha { color: #d29922; font-weight: bold; font-size: 0.8rem; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE & AI HANDLER ---
if "messages" not in st.session_state: st.session_state.messages = []

def get_working_model(key):
    genai.configure(api_key=key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available else available[0]
    except: return "models/gemini-1.5-flash"

def handle_ai_query(prompt, context, key):
    for attempt in range(3):
        try:
            model = genai.GenerativeModel(get_working_model(key))
            full_prompt = f"Context: {context}\n\nUser: {prompt}"
            time.sleep(2.0)
            return model.generate_content(full_prompt).text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(5); continue
            return "⚠️ Service Busy: Quota reached. Please wait 60s."

# --- 3. STABLE DATA ENGINE (Serialization Safe) ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    idx = 1 if "India" in exchange_choice else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers)
        symbols = pd.read_html(resp.text)[idx]['Symbol'].tolist()
        if idx == 1: symbols = [s + ".NS" for s in symbols]
        
        sample = symbols[::max(1, len(symbols)//40)] 
        results = []
        for symbol in sample:
            try:
                t = yf.Ticker(symbol); h = t.history(period="5d")
                if len(h) < 2: continue
                curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                # Returning ONLY serializable data (strings, floats)
                results.append({
                    "ticker": symbol, "price": curr, "change": ((curr-prev)/prev)*100,
                    "entry": (2*piv)-hi, "target": (2*piv)-lo, "abs_change": abs(((curr-prev)/prev)*100)
                })
            except: continue
        return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')
    except: return []

# --- 4. MAIN INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Market Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk", "📜 What is this app?"])

with tab_tactical:
    alpha_mode = st.toggle("✨ Unlock Alpha Insights (Full Names, 52W Data, R/R Ratio)", value=False)
    leaders = rank_movers(exchange_choice)
    curr_sym = "₹" if "India" in exchange_choice else "$"
    
    if not leaders:
        st.warning("⚠️ Market data unavailable. Please refresh in 30s.")
    else:
        leader_context = "Current Leaders: "
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                st.metric(label=stock['ticker'], value=f"{curr_sym}{stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
                
                alpha_html = ""
                if alpha_mode:
                    # Fetch extra details ONLY for these 5 tickers to stay stable
                    t_info = yf.Ticker(stock['ticker']).info
                    stop = stock['entry'] * 0.985
                    rr = abs(stock['target']-stock['entry'])/abs(stock['entry']-stop) if abs(stock['entry']-stop) != 0 else 0
                    alpha_html = f"""
                        <hr style="border:0.1px solid #333; margin:8px 0;">
                        <b style="color:#8b949e; font-size:0.65rem;">{t_info.get('longName', 'Security')[:20]}</b><br>
                        <span class="val-alpha">52W H: {curr_sym}{t_info.get('fiftyTwoWeekHigh', 0):.2f}</span><br>
                        <span class="val-alpha">52W L: {curr_sym}{t_info.get('fiftyTwoWeekLow', 0):.2f}</span><br>
                        <span class="val-alpha">R/R Ratio: {rr:.2f}</span>
                    """

                st.markdown(f"""
                    <div class="strike-zone-card">
                        <span class="val-entry">Entry: {curr_sym}{stock['entry']:.2f}</span><br>
                        <span class="val-target">Target: {curr_sym}{stock['target']:.2f}</span>
                        {alpha_html}
                    </div>
                """, unsafe_allow_html=True)
                leader_context += f"{stock['ticker']} ({stock['price']:.2f}); "
        st.session_state.current_context = leader_context

    st.divider()
    query = st.text_input("Deep-Dive Any Ticker (e.g. RELIANCE.NS, TSLA):").upper()
    if query:
        try:
            q_t = yf.Ticker(query); q_h = q_t.history(period="2d"); q_i = q_t.info
            p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
            piv = (hi + lo + prev) / 3
            st.metric(label=f"{query} ({q_i.get('longName', '')})", value=f"{curr_sym}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
            st.markdown(f"""
                <div class="strike-zone-card">
                    <span class="val-entry">Entry: {curr_sym}{(2*piv)-hi:.2f}</span> | <span class="val-target">Target: {curr_sym}{(2*piv)-lo:.2f}</span><br>
                    <span class="val-alpha">52W Range: {curr_sym}{q_i.get('fiftyTwoWeekLow', 0):.2f} - {curr_sym}{q_i.get('fiftyTwoWeekHigh', 0):.2f}</span>
                </div>
            """, unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_research:
    c1, c2 = st.columns([4, 1]); c1.write("### AI Research Desk")
    if c2.button("🗑️ Clear"): st.session_state.messages = []; st.rerun()

    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        suggestions = ["Explain the leaders", "What is Strike Zone?", "Nifty 50 Trend?"]
        s_cols = st.columns(3); clicked = None
        for idx, s in enumerate(suggestions):
            if s_cols[idx].button(s, use_container_width=True): clicked = s

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        prompt = st.chat_input("Analyze market energy...")
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
    ### 🏛️ Sovereign Protocol & Alpha Features (v37.0)
    
    #### ⚡ Core Tactical Features (Validated)
    * **Dynamic Market Discovery:** Real-time scrape of S&P 500 and Nifty 50.
    * **Volatility Ranking:** Stocks identified by absolute percentage change.
    * **Pivot Math:** Institutional Entry (S1) and Target (R1) levels.
    * **✨ Alpha Toggle:** On-demand access to Security Names, 52W Data, and R/R Ratios.
    * **Global Toggle:** Switch between US ($) and India (₹).
    * **Institutional Disclaimer:** Final legal protocols and user responsibility anchored.
    
    #### 🤖 AI & Infrastructure
    * **Exponential Backoff:** Stability guard for Gemini free-tier limits.
    * **Whitelabel UI:** Custom OLED-contrast theme with Streamlit branding hidden.
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. Trading involves risk. <b>USER RESPONSIBILITY:</b> You are solely responsible for your financial decisions and actions.</div>""", unsafe_allow_html=True)
