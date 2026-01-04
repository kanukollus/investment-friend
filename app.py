import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random
from google.api_core import exceptions

# --- 1. ARCHITECTURAL CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Terminal | GT Edition", layout="wide")

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

# --- 3. VEDIC DYNAMIC MODEL DISCOVERY ---
@st.cache_data(ttl=3600)
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Priority: Flash 1.5 for high-quota student stability
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash'
        return available[0]
    except Exception:
        return "models/gemini-1.5-flash"

# --- 4. RESILIENT AI HANDLER (Integrated generate_with_retry) ---
def generate_with_retry(prompt, context, api_key):
    model_name = get_working_model(api_key)
    model = genai.GenerativeModel(model_name)
    
    retries = 3
    delay = 2  # Start with a 2-second delay

    for i in range(retries):
        try:
            # Enhanced prompt with system context
            full_prompt = f"Context Snapshot: {context[:300]}\nUser Request: {prompt}"
            response = model.generate_content(full_prompt)
            
            if response and hasattr(response, 'text'):
                return response.text
            return "⚠️ Safety Filter: Content blocked by API."
        
        except exceptions.ResourceExhausted as e:
            if i < retries - 1:
                st.warning(f"Quota hit. Waiting {delay}s before retrying... (Attempt {i+1}/3)")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                return f"🚨 Max retries reached. Raw Error: {str(e)}"
        except Exception as e:
            return f"🚨 RAW ERROR: {str(e)}"

# --- 5. DATA ENGINE (v31.0 Base) ---
@st.cache_data(ttl=600)
def rank_movers(universe):
    idx = 1 if "India" in universe else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        syms = pd.read_html(resp.text)[idx]['Symbol'].tolist()
        if idx == 1: syms = [s + ".NS" for s in syms]
        results = []
        for s in syms[::max(1, len(syms)//40)]:
            try:
                t = yf.Ticker(s); h = t.history(period="2d")
                if len(h) < 2: continue
                c, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                p = (hi + lo + prev) / 3
                results.append({"ticker": s, "price": c, "change": ((c-prev)/prev)*100, "entry": (2*p)-hi, "target": (2*p)-lo, "abs": abs(((c-prev)/prev)*100)})
            except: continue
        return pd.DataFrame(results).sort_values(by='abs', ascending=False).head(5).to_dict('records')
    except: return []

# --- 6. INTERFACE ---
st.title("🏛️ Sovereign Terminal | GT Edition")
exch = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical", "🤖 AI Research", "📜 About"])

with tab_tactical:
    leaders = rank_movers(exch)
    sym = "₹" if "India" in exch else "$"
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
    search = st.text_input("Strategic Search (Ticker):", key=f"s_{exch}").upper()
    if search:
        try:
            q_t = yf.Ticker(search); q_h = q_t.history(period="2d")
            p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
            piv = (hi + lo + prev) / 3
            st.metric(label=search, value=f"{sym}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
            st.markdown(f"<div class='strike-zone-card'>Entry: {curr}{(2*piv)-hi:.2f} | Target: {curr}{(2*piv)-lo:.2f}</div>", unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_research:
    api_key = st.secrets.get("GEMINI_API_KEY")
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

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
                with st.spinner("Executing resilient AI request..."):
                    ans = generate_with_retry(final_query, st.session_state.current_context, api_key)
                    st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_about:
    st.write("### 🏛️ Sovereign Protocol & Features (v55.0)")
    st.markdown("""
    * **Exponential Backoff:** Integrated student-provided retry logic to handle `ResourceExhausted` errors.
    * **Vedic Model Discovery:** System audits API aliases to find valid content generators.
    * **Student Optimization:** Locked to **Gemini 1.5 Flash** for high-quota stability.
    * **Whitelabel UI:** Standard features preserved (Strategic Search, Universe Clearing).
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. <b>USER RESPONSIBILITY:</b> GT students are solely responsible for their financial decisions.</div>""", unsafe_allow_html=True)
