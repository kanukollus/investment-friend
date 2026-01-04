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
    /* 1. Global Stealth & Contrast Guard */
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    .stApp { background-color: #0d1117 !important; color: #FFFFFF !important; }
    
    /* 2. FIX: Menu & Tab Visibility (Resolves IMG_3192.jpg contrast issues) */
    button[data-baseweb="tab"] { color: #8b949e !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #58a6ff !important; border-bottom-color: #58a6ff !important; }
    
    /* 3. FIX: Button Visibility (Resolves IMG_3192.jpg white-on-white) */
    div[data-testid="stButton"] button {
        background-color: #1f2937 !important; 
        color: #FFFFFF !important;
        border: 1px solid #30363d !important;
        font-weight: 600 !important;
    }

    /* 4. Tactical Cards (IMG_3191.jpg/IMG_3193.jpg Optimization) */
    [data-testid="stMetric"] { 
        background-color: #161b22 !important; 
        border: 1px solid #30363d !important; 
        border-radius: 12px;
        padding: 1rem !important;
    }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #8b949e !important; }

    .strike-zone-card { 
        background-color: #0d1117; 
        border: 1px solid #30363d; 
        padding: 12px; 
        border-radius: 8px; 
        margin-top: 8px;
        font-family: 'Courier New', monospace;
    }
    .val-entry { color: #58a6ff !important; font-weight: bold; }
    .val-target { color: #3fb950 !important; font-weight: bold; }

    /* 5. Mobile Fluidity Scaling */
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        .stApp { padding: 10px !important; }
    }

    /* 6. Institutional Disclaimer - High Contrast Red */
    .disclaimer-box { 
        background-color: #1c1c1c !important; 
        border: 1px solid #f85149 !important; 
        padding: 15px !important; 
        border-radius: 8px !important; 
        color: #f85149 !important; 
        margin: 40px auto !important; 
        text-align: center !important;
        font-size: 0.85rem !important;
        font-weight: bold !important;
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
        leader_ctx = ""
        for i, s in enumerate(leaders):
            st.metric(label=s['ticker'], value=f"{curr}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
            st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr}{s['entry']:.2f}</span> | <span class='val-target'>Target: {curr}{s['target']:.2f}</span></div>", unsafe_allow_html=True)
            leader_ctx += f"{s['ticker']}:{s['price']}; "
        st.session_state.current_context = leader_ctx
    
    st.divider()
    search = st.text_input("Strategic Search:", key=f"s_{exch}").strip().upper()
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
                    with st.spinner("Analyzing..."):
                        model = genai.GenerativeModel(get_working_model(api_key))
                        thesis = model.generate_content(f"3-point bull thesis for {search}").text
                        st.markdown(f"### 📈 Thesis: {search}")
                        st.markdown(f"<div class='strike-zone-card'>{thesis}</div>", unsafe_allow_html=True)
        except: st.error("Ticker offline.")

with tab_r:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if st.button("🗑️ Reset Chat"): st.session_state.messages = []; st.rerun()
    
    s_cols = st.columns(3); clicked = None
    for idx, s in enumerate(["Analyze Movers", "Strike Zones", "Market Trend"]):
        if s_cols[idx].button(s, use_container_width=True): clicked = s

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    if prompt := st.chat_input("Ask Terminal..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking..."):
                model = genai.GenerativeModel(get_working_model(api_key))
                ans = model.generate_content(f"Context: {st.session_state.current_context}\nQ: {prompt}").text
                st.markdown(ans); st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_a:
    st.write("### 📜 Sovereign Protocol (v65.0)")
    st.markdown("* **Contrast Guard:** Explicitly locks HEX colors for menu items to prevent mobile 'Ghost' text.\n* **Fluid Stack:** Metrics stack vertically on mobile for better touch targeting.\n* **Pro Tier:** Optimized for billing-enabled API quotas (2,000 RPM).")

# --- GLOBAL DISCLAIMER ---
st.markdown("""<div class="disclaimer-box">⚠️ RISK WARNING: Trading involves significant risk. Users are solely responsible for financial decisions.</div>""", unsafe_allow_html=True)
