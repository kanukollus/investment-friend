import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
from google.api_core import exceptions

# --- 1. ARCHITECTURAL CONFIG & CONTRAST ENGINE ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* Global UI Stealth & Contrast */
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    .stApp { background-color: #0d1117 !important; color: #FFFFFF !important; }
    
    /* Universe & Search Visibility (v66 Fixed) */
    div[data-testid="stWidgetLabel"] p { color: #FFFFFF !important; font-weight: 600 !important; }
    div[data-testid="stRadio"] label { color: #FFFFFF !important; }
    div[data-testid="stTextInput"] label p { color: #58a6ff !important; font-weight: bold !important; }
    
    /* Menu & Tab Visibility */
    button[data-baseweb="tab"] { color: #8b949e !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #58a6ff !important; border-bottom-color: #58a6ff !important; }
    
    /* BUTTON INTERACTION FIX */
    div[data-testid="stButton"] button {
        background-color: #1f2937 !important; 
        color: #FFFFFF !important;
        border: 1px solid #30363d !important;
        font-weight: 600 !important;
        width: 100% !important;
        cursor: pointer !important;
    }

    /* Tactical Metrics */
    [data-testid="stMetric"] { background-color: #161b22 !important; border: 1px solid #30363d !important; border-radius: 12px; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 700 !important; }
    
    .strike-zone-card { 
        background-color: #0d1117; 
        border: 1px solid #30363d; 
        padding: 12px; 
        border-radius: 8px; 
        margin-top: 8px;
        font-family: monospace;
    }
    .val-entry { color: #58a6ff !important; }
    .val-target { color: #3fb950 !important; }

    /* Disclaimer High Contrast Red */
    .disclaimer-box { 
        background-color: #1c1c1c !important; 
        border: 1px solid #f85149 !important; 
        padding: 15px !important; 
        border-radius: 8px !important; 
        color: #f85149 !important; 
        margin-top: 40px !important;
        text-align: center !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE (Interaction Guard) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""
if "suggested_query" not in st.session_state: st.session_state.suggested_query = None

# --- 3. DYNAMIC MODEL DISCOVERY ---
@st.cache_data(ttl=3600)
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash'
        return available[0]
    except: return "models/gemini-1.5-flash"

# --- 4. DATA ENGINE ---
@st.cache_data(ttl=600)
def rank_movers(universe):
    idx = 1 if "India" in universe else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        syms = pd.read_html(resp.text)[idx]['Symbol'].tolist()
        if idx == 1: syms = [s + ".NS" for s in syms]
        res = []
        for s in syms[::max(1, len(syms)//40)]:
            try:
                t = yf.Ticker(s); h = t.history(period="2d")
                if len(h) < 2: continue
                c, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                p = (hi + lo + prev) / 3
                res.append({"ticker": s, "price": c, "change": ((c-prev)/prev)*100, "entry": (2*p)-hi, "target": (2*p)-lo, "abs": abs(((c-prev)/prev)*100)})
            except: continue
        return pd.DataFrame(res).sort_values(by='abs', ascending=False).head(5).to_dict('records')
    except: return []

# --- 5. INTERFACE ---
st.title("🏛️ Sovereign Terminal")
exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_t, tab_r, tab_a = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    leaders = rank_movers(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        leader_ctx = ""
        for i, s in enumerate(leaders):
            st.metric(label=s['ticker'], value=f"{curr}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
            st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr}{s['entry']:.2f}</span> | <span class='val-target'>Target: {curr}{s['target']:.2f}</span></div>", unsafe_allow_html=True)
            leader_ctx += f"{s['ticker']}:{s['price']}; "
        st.session_state.current_context = leader_ctx
    
    st.divider()
    search = st.text_input("Strategic Search (Ticker):", key=f"s_{exch}").strip().upper()
    if search:
        api_key = st.secrets.get("GEMINI_API_KEY")
        try:
            q_t = yf.Ticker(search); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                st.metric(label=search, value=f"{curr}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr}{(2*piv)-hi:.2f}</span> | <span class='val-target'>Target: {curr}{(2*piv)-lo:.2f}</span></div>", unsafe_allow_html=True)
                if api_key:
                    with st.spinner(f"🧠 Advisor processing {search}..."):
                        model = genai.GenerativeModel(get_working_model(api_key))
                        thesis = model.generate_content(f"3-point bull thesis for {search}").text
                        st.markdown(f"### 📈 Thesis: {search}")
                        st.markdown(f"<div class='strike-zone-card'>{thesis}</div>", unsafe_allow_html=True)
        except: st.error("Ticker offline.")

with tab_r:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if st.button("🗑️ Reset Chat", key="clear_chat_btn"): 
        st.session_state.messages = []
        st.session_state.suggested_query = None
        st.rerun()
    
    # 🏛️ INTERACTION FIX: Assigning specific keys to buttons
    s_cols = st.columns(3)
    s_list = ["Analyze Movers", "Strike Zones", "Market Trend"]
    for idx, s in enumerate(s_list):
        if s_cols[idx].button(s, key=f"s_btn_{idx}", use_container_width=True): 
            st.session_state.suggested_query = s

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    chat_prompt = st.chat_input("Ask Terminal...")
    
    # Logic to capture either the button click or the manual input
    final_q = st.session_state.suggested_query if st.session_state.suggested_query else chat_prompt

    if final_q:
        st.session_state.messages.append({"role": "user", "content": final_q})
        # Clear the suggestion immediately so it doesn't loop
        st.session_state.suggested_query = None
        with st.chat_message("user"): st.write(final_q)
        with st.chat_message("assistant"):
            with st.spinner("🧠 Intelligence Processing..."):
                model = genai.GenerativeModel(get_working_model(api_key))
                ans = model.generate_content(f"Context: {st.session_state.current_context}\nQ: {final_q}").text
                st.markdown(ans); st.session_state.messages.append({"role": "assistant", "content": ans})
        st.rerun() # Refresh to update chat display

with tab_a:
    st.write("### 📜 Sovereign Protocol (v67.0)")
    st.markdown("""
    * **Interaction Guard:** Assigned unique persistent keys to all buttons to fix unclickable UI issues.
    * **State Refresh:** Implemented a targeted `st.rerun()` loop to ensure the chat history updates instantly.
    * **Contrast Lock:** Maintained high-contrast white/blue labels for all tactical inputs.
    """)

# --- GLOBAL DISCLAIMER ---
st.markdown("""<div class="disclaimer-box">⚠️ RISK WARNING: Financial trading involves high risk. All decisions are the responsibility of the user.</div>""", unsafe_allow_html=True)
