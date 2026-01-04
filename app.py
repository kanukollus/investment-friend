import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")
st.markdown("""<style>
    header, footer, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; height: 0; }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; }
</style>""", unsafe_allow_html=True)

# --- 2. VEDIC DISCOVERY: 1.5 PRIORITY ---
@st.cache_data(ttl=3600)
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # ARCHITECT'S MOVE: Lock to 1.5-Flash (1,500 RPD) vs 2.5-Flash (20 RPD)
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash'
        return available[0]
    except: return "models/gemini-1.5-flash"

# --- 3. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 4. DATA ENGINE (v31.0 Base) ---
@st.cache_data(ttl=600)
def rank_movers(exch):
    idx = 1 if "India" in exch else 0
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
st.title("🏛️ Sovereign Intelligence Terminal")
exch = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)
tab_t, tab_r, tab_a = st.tabs(["⚡ Tactical", "🤖 AI Desk", "📜 About"])

with tab_t:
    leaders = rank_movers(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        leader_ctx = ""
        cols = st.columns(5)
        for i, s in enumerate(leaders):
            with cols[i]:
                st.metric(label=s['ticker'], value=f"{curr}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr}{s['entry']:.2f}</span><br><span class='val-target'>Target: {curr}{s['target']:.2f}</span></div>", unsafe_allow_html=True)
                leader_ctx += f"{s['ticker']}:{s['price']}; "
        st.session_state.current_context = leader_ctx
    st.divider()
    search = st.text_input("Strategic Search:", key=f"s_{exch}").upper()
    if search:
        try:
            q_t = yf.Ticker(search); q_h = q_t.history(period="2d")
            p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
            piv = (hi + lo + prev) / 3
            st.metric(label=search, value=f"{curr}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
            st.markdown(f"<div class='strike-zone-card'>Entry: {curr}{(2*piv)-hi:.2f} | Target: {curr}{(2*piv)-lo:.2f}</div>", unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_r:
    key = st.secrets.get("GEMINI_API_KEY")
    if st.button("🗑️ Clear"): st.session_state.messages = []; st.rerun()
    s_cols = st.columns(3); clicked = None
    for i, s in enumerate(["Analyze leaders", "Strike Zone?", "Trend?"]):
        if s_cols[i].button(s, use_container_width=True): clicked = s
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    prompt = st.chat_input("Analyze...")
    final = clicked if clicked else prompt
    if final:
        st.session_state.messages.append({"role": "user", "content": final})
        with st.chat_message("user"): st.write(final)
        with st.chat_message("assistant"):
            try:
                model = genai.GenerativeModel(get_working_model(key))
                ans = model.generate_content(f"Data: {st.session_state.current_context[:300]}\nQ: {final}").text
                st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e: st.write(f"🚨 RAW ERROR: {str(e)}")

with tab_a:
    st.write("### 🏛️ Sovereign Protocol (v51.0)")
    st.markdown("* **Stability Lock:** Forces **Gemini 1.5 Flash** to maintain a higher free-tier quota (1,500 RPD).\n* **Strategic Search:** Integrated Entry/Target math with universe-aware auto-clear.\n* **State Persistence:** Guarded session initialization prevents AttributeError crashes.")

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. <b>USER RESPONSIBILITY:</b> You are solely responsible for your financial decisions.</div>""", unsafe_allow_html=True)
