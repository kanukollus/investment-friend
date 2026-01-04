import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
from google.api_core import exceptions

# --- 1. ARCHITECTURAL CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; height: 0; }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .thesis-box { background-color: #161b22; border-left: 4px solid #58a6ff; padding: 15px; margin-top: 10px; border-radius: 0 8px 8px 0; font-size: 0.9rem; line-height: 1.6; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE GUARD ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. VEDIC DYNAMIC MODEL DISCOVERY (The Permanent Fix for 404) ---
@st.cache_data(ttl=3600)
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Professional Tier Choice: 1.5-Flash is most stable
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash'
        if 'models/gemini-1.5-flash-latest' in available: return 'models/gemini-1.5-flash-latest'
        return available[0]
    except Exception:
        return "models/gemini-1.5-flash"

# --- 4. RESILIENT AI HANDLER ---
def handle_ai_query(prompt, context, api_key):
    model_name = get_working_model(api_key)
    model = genai.GenerativeModel(model_name)
    try:
        full_prompt = f"Market Data: {context[:400]}\nQuery: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text if response and hasattr(response, 'text') else "⚠️ No response generated."
    except Exception as e:
        return f"🚨 RAW ERROR: {str(e)}"

# --- 5. DATA ENGINE ---
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

# --- 6. MAIN UI ---
st.title("🏛️ Sovereign Intelligence Terminal")
exch = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_tactical:
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
                        thesis = handle_ai_query(f"Provide 3-point bullish thesis for {search}", "", api_key)
                        st.markdown(f"### 📈 Thesis: {search}")
                        st.markdown(f"<div class='thesis-box'>{thesis}</div>", unsafe_allow_html=True)
        except: st.error("Search failed.")

with tab_research:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if st.button("🗑️ Clear Intelligence"): st.session_state.messages = []; st.rerun()

    # 🏛️ RESTORED: AI SUGGESTIONS
    suggestions = ["Analyze current leaders", "Identify Strike Zones", "Market Rationale"]
    s_cols = st.columns(3); clicked_s = None
    for idx, s in enumerate(suggestions):
        if s_cols[idx].button(s, use_container_width=True): clicked_s = s

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    prompt = st.chat_input("Ask Terminal...")
    final_query = clicked_s if clicked_s else prompt

    if final_query:
        st.session_state.messages.append({"role": "user", "content": final_query})
        with st.chat_message("user"): st.write(final_query)
        with st.chat_message("assistant"):
            if not api_key: st.error("API Key Missing.")
            else:
                ans = handle_ai_query(final_query, st.session_state.current_context, api_key)
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_about:
    st.write("### 🏛️ Sovereign Protocol & Stability (v60.0)")
    st.markdown("""
    * **404 Suppression:** Fixed hardcoded model strings to use dynamic discovery.
    * **AI Suggestions:** Restored button-based research shortcuts.
    * **Billing Tier:** Optimized for professional quotas (2,000 RPM).
    """)
