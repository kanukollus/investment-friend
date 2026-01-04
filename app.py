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
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
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

# --- 3. VEDIC MODEL DISCOVERY ---
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in available_models: return 'models/gemini-1.5-flash'
        return available_models[0] if available_models else "models/gemini-1.5-flash"
    except Exception as e:
        return f"ERROR_DISCOVERY: {str(e)}"

# --- 4. TRANSPARENT AI HANDLER (Returns Raw Exceptions) ---
def handle_ai_query(prompt, context, key):
    model_name = get_working_model(key)
    if "ERROR_DISCOVERY" in model_name:
        return model_name
        
    try:
        model = genai.GenerativeModel(model_name)
        # Minimize context to reduce "None" failures caused by over-tokenization
        response = model.generate_content(f"Market: {context[:300]}\nQuery: {prompt}")
        
        if hasattr(response, 'text'):
            return response.text
        else:
            # Handle cases where safety filters block the response
            return f"⚠️ SAFETY BLOCK OR EMPTY: {str(response.prompt_feedback)}"
            
    except Exception as e:
        # RETURN RAW EXCEPTION AS REQUESTED
        return f"🚨 RAW SYSTEM ERROR: {str(e)}"

# --- 5. DATA ENGINE (v31.0 Base) ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    idx = 1 if "India" in exchange_choice else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        symbols = pd.read_html(response.text)[idx]['Symbol'].tolist()
        if idx == 1: symbols = [s + ".NS" for s in symbols]
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

# --- 6. MAIN UI ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical", "🤖 AI Desk", "📜 About"])

with tab_tactical:
    leaders = rank_movers(exchange_choice)
    curr_sym = "₹" if "India" in exchange_choice else "$"
    if leaders:
        leader_ctx = ""
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                st.metric(label=stock['ticker'], value=f"{curr_sym}{stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr_sym}{stock['entry']:.2f}</span><br><span class='val-target'>Target: {curr_sym}{stock['target']:.2f}</span></div>", unsafe_allow_html=True)
                leader_ctx += f"{stock['ticker']}:{stock['price']}; "
        st.session_state.current_context = leader_ctx

    st.divider()
    search_q = st.text_input("Strategic Search (Ticker):", key=f"search_{exchange_choice}").upper()
    if search_q:
        try:
            q_t = yf.Ticker(search_q); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                st.metric(label=search_q, value=f"{curr_sym}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr_sym}{(2*piv)-hi:.2f}</span><br><span class='val-target'>Target: {curr_sym}{(2*piv)-lo:.2f}</span></div>", unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_research:
    api_key = st.secrets.get("GEMINI_API_KEY")
    c1, c2 = st.columns([4, 1]); c1.write("### AI Research Desk")
    if c2.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

    suggestions = ["Analyze the leaders", "Define Strike Zone", "Market Trend?"]
    s_cols = st.columns(3); clicked = None
    for idx, s in enumerate(suggestions):
        if s_cols[idx].button(s, use_container_width=True): clicked = s

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    prompt = st.chat_input("Analyze the tape...")
    final_query = clicked if clicked else prompt

    if final_query:
        st.session_state.messages.append({"role": "user", "content": final_query})
        with st.chat_message("user"): st.write(final_query)
        with st.chat_message("assistant"):
            if not api_key: st.error("Missing API Key.")
            else:
                ans = handle_ai_query(final_query, st.session_state.current_context, api_key)
                # Output the response (or the Raw Error)
                st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_about:
    st.write("### 🏛️ Sovereign Protocol & Features")
    st.markdown("""
    **Sovereign Intelligence Terminal (v49.0 - Debug Mode)**
    
    #### 🛠️ Transparency Features
    * **Raw Exception Reporting:** AI handler now returns original system errors for precise debugging.
    * **Safety Filter Awareness:** Explicitly reports if a query was blocked by Gemini's internal filters.
    * **State Guard Protection:** Architectural fix for AttributeError crashes.
    * **Vedic Model Discovery:** Corrected model handshake for `v1beta` support.
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. <b>USER RESPONSIBILITY:</b> You are solely responsible for your financial decisions.</div>""", unsafe_allow_html=True)
