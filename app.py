import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random

# --- 1. ARCHITECTURAL CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* UI Stealth Mode */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* Tactical Metric Styling */
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE GUARD ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. STABLE AI HANDLER (Locking to 1.5 Flash) ---
def handle_ai_query(prompt, context, key):
    genai.configure(api_key=key)
    # Architectural Lock: Fixed to 1.5-Flash for 1,500 RPD free quota
    model_name = "gemini-1.5-flash" 
    
    try:
        model = genai.GenerativeModel(model_name)
        # Token conservation: short context snapshot
        response = model.generate_content(f"Tape Snapshot: {context[:300]}\nAdvisor Query: {prompt}")
        if response and hasattr(response, 'text'):
            return response.text
        return "⚠️ Safety Filter: The response was blocked by Gemini's safety settings."
    except Exception as e:
        # Transparent Error Reporting
        return f"🚨 RAW SYSTEM ERROR: {str(e)}"

# --- 4. DATA ENGINE (v31.0 Base - Stable) ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    idx = 1 if "India" in exchange_choice else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers)
        symbols = pd.read_html(resp.text)[idx]['Symbol'].tolist()
        if idx == 1: symbols = [s + ".NS" for s in symbols]
        
        # Sampling logic to prevent rate-limiting the data provider
        sample = symbols[::max(1, len(symbols)//40)] 
        results = []
        for symbol in sample:
            try:
                t = yf.Ticker(symbol); h = t.history(period="2d")
                if len(h) < 2: continue
                curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                results.append({
                    "ticker": symbol, "price": curr, "change": ((curr-prev)/prev)*100,
                    "entry": (2*piv)-hi, "target": (2*piv)-lo, "abs_change": abs(((curr-prev)/prev)*100)
                })
            except: continue
        return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')
    except: return []

# --- 5. INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")

# Universe Control
exchange_choice = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical", "🤖 AI Desk", "📜 About"])

with tab_tactical:
    leaders = rank_movers(exchange_choice)
    curr_sym = "₹" if "India" in exchange_choice else "$"
    
    if not leaders:
        st.warning("⚠️ Market link resetting. Please refresh in 30s.")
    else:
        leader_ctx = ""
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                st.metric(label=stock['ticker'], value=f"{curr_sym}{stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
                st.markdown(f"""
                    <div class='strike-zone-card'>
                        <span class='val-entry'>Entry: {curr_sym}{stock['entry']:.2f}</span><br>
                        <span class='val-target'>Target: {curr_sym}{stock['target']:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                leader_ctx += f"{stock['ticker']}:{stock['price']}; "
        st.session_state.current_context = leader_ctx

    st.divider()
    
    # Tactical Search (Auto-clears on Universe Switch)
    search_q = st.text_input("Strategic Search (Ticker):", key=f"s_{exchange_choice}").upper()
    if search_q:
        try:
            q_t = yf.Ticker(search_q); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                st.metric(label=search_q, value=f"{curr_sym}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"<div class='strike-zone-card'>Entry: {curr_sym}{(2*piv)-hi:.2f} | Target: {curr_sym}{(2*piv)-lo:.2f}</div>", unsafe_allow_html=True)
            else: st.error("No data for this ticker.")
        except: st.error("Search Feed Unavailable.")

with tab_research:
    api_key = st.secrets.get("GEMINI_API_KEY")
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

    # Regression Check: AI Suggestions restored
    suggestions = ["Analyze the leaders", "Define Strike Zone", "Trend Analysis"]
    s_cols = st.columns(3); clicked = None
    for idx, s in enumerate(suggestions):
        if s_cols[idx].button(s, use_container_width=True): clicked = s

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    prompt = st.chat_input("Ask about the tape...")
    final_query = clicked if clicked else prompt

    if final_query:
        st.session_state.messages.append({"role": "user", "content": final_query})
        with st.chat_message("user"): st.write(final_query)
        with st.chat_message("assistant"):
            if not api_key: st.error("Missing API Key.")
            else:
                ans = handle_ai_query(final_query, st.session_state.current_context, api_key)
                st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_about:
    st.write("### 🏛️ Sovereign Intelligence Terminal (v52.0)")
    st.markdown("""
    #### 🛡️ Architectural Stabilizers
    * **Stability Lock:** Terminal is forced to **Gemini 1.5 Flash**.
    * **High Quota Tier:** Accesses up to **1,500 requests per day** for free.
    * **Zero-Burst Logic:** AI invocation is manual-only to prevent "Ghost" requests.
    
    #### ⚡ Core Tactical Features
    * **Strategic Search:** Universal ticker search with integrated **Entry/Target math**.
    * **Volatility Engine:** Real-time ranking of S&P 500 and Nifty 50 movers.
    * **Institutional Math:** Automated Floor Trader Pivot Points ($S1$/$R1$).
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. <b>USER RESPONSIBILITY:</b> You are solely responsible for your financial decisions.</div>""", unsafe_allow_html=True)
