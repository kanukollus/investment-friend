import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
from google.api_core import exceptions

# --- 1. ARCHITECTURAL CONFIG & RESPONSIVE THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* 1. Global UI Stealth - Precise targeting to avoid hiding the Disclaimer */
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; 
    }
    
    /* 2. Mobile & Desktop Color Correction (Fixes White-on-White text) */
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* Force Button Text Visibility for Research Desk */
    div[data-testid="stButton"] button {
        background-color: #161b22 !important;
        color: #f0f6fc !important;
        border: 1px solid #30363d !important;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #58a6ff !important;
        color: #58a6ff !important;
    }

    /* 3. Responsive Metric & Card Layouts */
    [data-testid="stMetric"] { 
        background-color: #161b22; 
        border: 1px solid #30363d; 
        padding: 1rem !important; 
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #8b949e !important; }
    
    .strike-zone-card { 
        background-color: #010409; 
        border: 1px solid #444c56; 
        padding: 12px; 
        border-radius: 10px; 
        margin-top: 8px; 
        font-family: monospace;
    }
    
    /* 4. Mobile Refinements (< 768px) */
    @media (max-width: 768px) {
        div[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        .thesis-box { font-size: 0.85rem !important; }
        .disclaimer-box { font-size: 0.7rem !important; padding: 12px !important; }
    }

    /* 5. Fixed Disclaimer & Thesis Boxes */
    .thesis-box { 
        background-color: #161b22; 
        border-left: 4px solid #58a6ff; 
        padding: 15px; 
        margin-top: 15px; 
        border-radius: 0 8px 8px 0; 
        font-size: 0.95rem; 
        line-height: 1.6; 
    }
    
    /* Explicitly visible disclaimer box */
    .disclaimer-box { 
        background-color: #1c1c1c !important; 
        border: 1px solid #ff4b4b !important; 
        padding: 20px !important; 
        border-radius: 8px !important; 
        font-size: 0.85rem !important; 
        color: #ff4b4b !important; 
        margin: 40px 0 !important; 
        text-align: center !important;
        display: block !important;
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
        # Use columns for desktop; Streamlit stacks them on mobile
        cols = st.columns(len(leaders))
        leader_ctx = ""
        for i, s in enumerate(leaders):
            with cols[i]:
                st.metric(label=s['ticker'], value=f"{curr}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span style='color:#58a6ff'>Entry: {curr}{s['entry']:.2f}</span><br><span style='color:#3fb950'>Target: {curr}{s['target']:.2f}</span></div>", unsafe_allow_html=True)
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
                    with st.spinner("Generating Thesis..."):
                        model = genai.GenerativeModel(get_working_model(api_key))
                        thesis = model.generate_content(f"3-point bullish thesis for {search}").text
                        st.markdown(f"<div class='thesis-box'><b>📈 Thesis: {search}</b><br>{thesis}</div>", unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_r:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if st.button("🗑️ Clear Intelligence"): st.session_state.messages = []; st.rerun()
    
    # Corrected Contrast Buttons
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
            model = genai.GenerativeModel(get_working_model(api_key))
            ans = model.generate_content(f"Market: {st.session_state.current_context}\nQ: {final}").text
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_a:
    st.write("### 📜 Sovereign Protocol (v62.0)")
    st.markdown("""
    * **Contrast Shield:** Overrides mobile browser defaults to fix white-on-white text issues.
    * **Fluid Responsiveness:** Dynamic font scaling for metric values and labels on smaller screens.
    * **Institutional Disclaimer:** Hard-coded visibility guard to prevent the disclaimer from being hidden.
    """)

# 🏛️ GLOBAL INSTITUTIONAL DISCLAIMER (Locked visibility)
st.markdown("""
<div class="disclaimer-box">
    <b>⚠️ INSTITUTIONAL RISK WARNING</b><br>
    Trading involve significant risk. Past performance is not indicative of future results. 
    Users are solely responsible for all financial decisions made using this terminal.
</div>
""", unsafe_allow_html=True)
