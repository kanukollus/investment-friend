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

# --- 2. STATE GUARD ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. OPTIMIZED VEDIC DISCOVERY (Shields against 2.5 Daily Caps) ---
# --- 3. VEDIC DISCOVERY: STRICT STABILITY LOCKDOWN ---
@st.cache_data(ttl=3600)
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 🏛️ ARCHITECT'S MOVE: Explicitly Blacklist Experimental Models
        # This prevents the "0 Limit" crash you are experiencing.
        blacklist = ['2.0', 'exp', 'experimental', 'thinking']
        
        # PRIORITY 1: Force Lock to 1.5-Flash (The current Stability King for Free Tiers)
        # 1.5-Flash allows ~15 RPM and 1,500 RPD.
        if 'models/gemini-1.5-flash' in available_models:
            return 'models/gemini-1.5-flash'
            
        # PRIORITY 2: Any non-experimental stable model
        for m in available_models:
            if not any(word in m.lower() for word in blacklist):
                return m
                
        # Final fallback to standard Flash 1.5
        return "models/gemini-1.5-flash"
    except Exception as e:
        return "models/gemini-1.5-flash"

# --- 4. TRANSPARENT AI HANDLER (Transparency First) ---
def handle_ai_query(prompt, context, key):
    model_name = get_working_model(key)
    if "ERROR" in model_name: return model_name
    
    try:
        model = genai.GenerativeModel(model_name)
        # Context Truncation to save TPM (Tokens Per Minute)
        response = model.generate_content(f"Market Snapshot: {context[:300]}\nUser Question: {prompt}")
        if hasattr(response, 'text'): return response.text
        return f"⚠️ SAFETY BLOCK: {str(response.prompt_feedback)}"
    except Exception as e:
        return f"🚨 RAW SYSTEM ERROR: {str(e)}"

# --- 5. DATA ENGINE (v31.0 Base - Stable) ---
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
        for s in sample:
            try:
                t = yf.Ticker(s); h = t.history(period="2d")
                if len(h) < 2: continue
                c, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                p = (hi + lo + prev) / 3
                results.append({"ticker": s, "price": c, "change": ((c-prev)/prev)*100, "entry": (2*p)-hi, "target": (2*p)-lo, "abs_change": abs(((c-prev)/prev)*100)})
            except: continue
        return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')
    except: return []

# --- 6. INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical", "🤖 AI Desk", "📜 About"])

with tab_tactical:
    leaders = rank_movers(exchange_choice)
    sym = "₹" if "India" in exchange_choice else "$"
    if leaders:
        leader_ctx = ""
        cols = st.columns(5)
        for i, s in enumerate(leaders):
            with cols[i]:
                st.metric(label=s['ticker'], value=f"{sym}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {sym}{s['entry']:.2f}</span><br><span class='val-target'>Target: {sym}{s['target']:.2f}</span></div>", unsafe_allow_html=True)
                leader_ctx += f"{s['ticker']}:{s['price']}; "
        st.session_state.current_context = leader_ctx
    
    st.divider()
    search = st.text_input("Strategic Search (Ticker):", key=f"search_{exchange_choice}").upper()
    if search:
        try:
            q_t = yf.Ticker(search); q_h = q_t.history(period="2d")
            p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
            piv = (hi + lo + prev) / 3
            st.metric(label=search, value=f"{sym}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
            st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {sym}{(2*piv)-hi:.2f}</span><br><span class='val-target'>Target: {sym}{(2*piv)-lo:.2f}</span></div>", unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_research:
    api_key = st.secrets.get("GEMINI_API_KEY")
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

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
                st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_about:
    st.write("### 🏛️ Sovereign Protocol & Features")
    st.markdown("""
    **Sovereign Intelligence Terminal (v50.0 - Optimized)**
    
    #### 🛡️ Quota Shields
    * **Model Lockdown:** Terminal ignores restrictive 2.5 models and locks onto high-limit **Gemini 1.5-Flash**.
    * **Discovery Caching:** `get_working_model` is cached for 1 hour to prevent background request waste.
    * **Zero-Burst Logic:** AI invocation is strictly manual-only; no background analysis runs.
    
    #### ⚡ Tactical Core
    * **Strategic Search Logic:** Entry/Target math integrated with universe-aware clearing.
    * **Institutional Math:** Automated Floor Trader Pivot Points ($S1$/$R1$).
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. <b>USER RESPONSIBILITY:</b> You are solely responsible for your financial decisions.</div>""", unsafe_allow_html=True)
