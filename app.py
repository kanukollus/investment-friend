import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
from google.api_core import exceptions

# --- 1. ARCHITECTURAL CONFIG & HIGH-CONTRAST THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    
    /* 1. Global Contrast Guard */
    .stApp { background-color: #0d1117 !important; color: #FAFAFA !important; }
    
    /* 2. Top 5 Picks - High-Contrast Card Styling */
    [data-testid="stMetric"] { 
        background-color: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 12px;
        padding: 1.2rem !important;
    }
    
    /* Force high-contrast text on Metrics */
    [data-testid="stMetricLabel"] { color: #B0B0B0 !important; font-size: 0.9rem !important; }
    [data-testid="stMetricValue"] { color: #FAFAFA !important; font-weight: 800 !important; }

    /* 3. Strike Zone Card - Desaturated Slate */
    .strike-zone-card { 
        background-color: #1f2937; /* Desaturated Slate */
        border: 1px solid #4b5563; 
        padding: 14px; 
        border-radius: 10px; 
        margin-top: 10px; 
        font-family: monospace;
        color: #E0E0E0 !important;
    }
    .val-entry { color: #60a5fa !important; font-weight: bold; } /* Desaturated Blue */
    .val-target { color: #34d399 !important; font-weight: bold; } /* Desaturated Green */

    /* 4. Thinking Spinner UI */
    .stSpinner { color: #58a6ff !important; font-family: monospace; }

    /* 5. Mobile Adjustments (< 768px) */
    @media (max-width: 768px) {
        div[data-testid="stMetricValue"] { font-size: 1.25rem !important; }
        .strike-zone-card { font-size: 0.8rem !important; }
    }

    /* 6. Professional Disclaimer Guard */
    .disclaimer-box { 
        background-color: #1c1c1c !important; 
        border: 1px solid #ef4444 !important; 
        padding: 18px !important; 
        border-radius: 10px !important; 
        color: #f87171 !important; 
        margin: 40px auto !important; 
        text-align: center !important;
        font-weight: 600 !important;
        max-width: 850px;
        visibility: visible !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

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
exch = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_t, tab_r, tab_a = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    leaders = rank_movers(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        cols = st.columns(len(leaders))
        leader_ctx = ""
        for i, s in enumerate(leaders):
            with cols[i]:
                st.metric(label=s['ticker'], value=f"{curr}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr}{s['entry']:.2f}</span><br><span class='val-target'>Target: {curr}{s['target']:.2f}</span></div>", unsafe_allow_html=True)
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
                st.markdown(f"<div class='strike-zone-card'>Entry: {curr}{(2*piv)-hi:.2f} | Target: {curr}{(2*piv)-lo:.2f}</div>", unsafe_allow_html=True)
                if api_key:
                    # 🏛️ THINKING GUARD
                    with st.spinner(f"AI Advisor is thinking about {search}..."):
                        model = genai.GenerativeModel(get_working_model(api_key))
                        thesis = model.generate_content(f"3-point investment thesis for {search}").text
                        st.markdown(f"### 📈 Thesis: {search}")
                        st.markdown(f"<div class='strike-zone-card'>{thesis}</div>", unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_r:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if st.button("🗑️ Clear Intelligence"): st.session_state.messages = []; st.rerun()
    
    s_cols = st.columns(3); clicked = None
    for idx, s in enumerate(["Analyze movers", "Strike Zones", "Trend Analysis"]):
        if s_cols[idx].button(s, use_container_width=True): clicked = s

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    prompt = st.chat_input("Ask Terminal...")
    final = clicked if clicked else prompt
    if final:
        st.session_state.messages.append({"role": "user", "content": final})
        with st.chat_message("user"): st.write(final)
        with st.chat_message("assistant"):
            # 🏛️ THINKING GUARD
            with st.spinner("Sovereign Intelligence is thinking..."):
                model = genai.GenerativeModel(get_working_model(api_key))
                ans = model.generate_content(f"Context: {st.session_state.current_context}\nQuery: {final}").text
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_a:
    st.write("### 📜 Sovereign Protocol (v64.0 Professional)")
    st.markdown("""
    * **Contrast Logic:** Switched white to **Off-White (#FAFAFA)** and **Slate (#1F2937)** for mobile clarity.
    * **Thinking Guard:** Implemented `st.spinner` for all AI interactions to provide visual feedback.
    * **Fluid Scaling:** Adjusted metric padding and sizing for high-density mobile screens.
    """)

# 🏛️ GLOBAL INSTITUTIONAL DISCLAIMER
st.markdown("""
<div class="disclaimer-box">
    <b>⚠️ INSTITUTIONAL RISK WARNING</b><br>
    Information is for research purposes only. 
    Users are solely responsible for all financial decisions made using this terminal.
</div>
""", unsafe_allow_html=True)
