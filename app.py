import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# --- 1. ARCHITECTURAL CONFIG & ADAPTIVE THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    
    /* Desktop Mode (Dark) */
    .stApp { background-color: #0d1117; color: #FFFFFF; }
    div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }
    div[data-testid="stButton"] button { background-color: #21262d; color: #58a6ff; border: 1px solid #30363d; }

    /* Mobile Mode (Light) Override */
    @media (max-width: 768px) {
        .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
        div[data-testid="stWidgetLabel"] p, [data-testid="stMetricLabel"] { color: #000000 !important; font-weight: 700 !important; }
        div[data-testid="stMetricValue"] { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
        div[data-testid="stMetric"] { background-color: #f6f8fa !important; border: 1px solid #d0d7de !important; }
        div[data-testid="stButton"] button {
            background-color: #eeeeee !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }
        [data-testid="stChatMessage"] { background-color: #f0f2f6 !important; border: 1px solid #d0d7de !important; }
        [data-testid="stChatMessage"] p { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    }

    .strike-zone-box { 
        background-color: #1f2937; 
        border: 1px solid #4b5563; 
        padding: 12px; 
        border-radius: 8px; 
        margin-top: 8px; 
        font-family: monospace; 
    }
    
    .disclaimer-box { 
        background-color: #1c1c1c; border: 1px solid #f85149; padding: 15px; 
        border-radius: 8px; color: #f85149; margin-top: 40px; text-align: center; font-weight: bold; 
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. REINFORCED GLOBAL STATE GUARD ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if "current_context" not in st.session_state: st.session_state["current_context"] = ""
if "suggested_query" not in st.session_state: st.session_state["suggested_query"] = None

# --- 3. AI & DATA ENGINES ---
@st.cache_data(ttl=3600)
def get_working_model(api_key):
    genai.configure(api_key=api_key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available else available[0]
    except: return "models/gemini-1.5-flash"

@st.cache_data(ttl=600)
def rank_movers(universe):
    """Identifies the 'Overstated' top movers and calculates Strike Zones."""
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
                # PIVOT MATH
                p = (hi + lo + prev) / 3
                res.append({
                    "ticker": s, "price": c, "change": ((c-prev)/prev)*100, 
                    "entry": (2*p)-hi, "target": (2*p)-lo, "abs": abs(((c-prev)/prev)*100)
                })
            except: continue
        return pd.DataFrame(res).sort_values(by='abs', ascending=False).head(5).to_dict('records')
    except: return []

# --- 4. MAIN INTERFACE ---
st.title("🏛️ Sovereign Terminal")
exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)
leaders = rank_movers(exch)

tab_t, tab_r, tab_a = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    curr = "₹" if "India" in exch else "$"
    if leaders:
        leader_ctx = ""
        for i, s in enumerate(leaders):
            # 🏛️ OVERSTATED INDICATOR: Highlights extreme moves
            status = "🔥 OVERSTATED" if abs(s['change']) > 4.0 else "⚡ VOLATILE"
            st.metric(label=f"{s['ticker']} ({status})", value=f"{curr}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
            
            # 🏛️ STRIKE ZONE RESTORED
            st.markdown(f"""
            <div class="strike-zone-box">
                <span style="color:#58a6ff; font-weight:bold;">Entry (S1): {curr}{s['entry']:.2f}</span> | 
                <span style="color:#3fb950; font-weight:bold;">Target (R1): {curr}{s['target']:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
            leader_ctx += f"{s['ticker']}:{s['price']}; "
        st.session_state["current_context"] = leader_ctx
    
    st.divider()
    search = st.text_input("Strategic Search (Ticker):", key=f"search_{exch}").strip().upper()
    if search:
        api_key = st.secrets.get("GEMINI_API_KEY")
        try:
            q_t = yf.Ticker(search); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p_c, prev_c, p_h, p_l = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                p_pt = (p_h + p_l + prev_c) / 3
                st.metric(label=search, value=f"{curr}{p_c:.2f}", delta=f"{((p_c-prev_c)/prev_c)*100:.2f}%")
                st.markdown(f'<div class="strike-zone-box"><span style="color:#58a6ff; font-weight:bold;">Entry: {curr}{(2*p_pt)-p_h:.2f}</span> | <span style="color:#3fb950; font-weight:bold;">Target: {curr}{(2*p_pt)-p_l:.2f}</span></div>', unsafe_allow_html=True)
                if api_key:
                    with st.spinner("🧠 Advisor thinking..."):
                        model = genai.GenerativeModel(get_working_model(api_key))
                        thesis = model.generate_content(f"3-point bull thesis for {search}").text
                        st.markdown(f"### 📈 Thesis: {search}")
                        st.markdown(f"<div style='background:#f6f8fa; border-left:4px solid #005cc5; padding:15px; color:#000000;'>{thesis}</div>", unsafe_allow_html=True)
        except: st.error("Ticker offline.")

with tab_r:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if st.button("🗑️ Reset Chat", key="clear_chat_btn"): 
        st.session_state["messages"] = []; st.session_state["suggested_query"] = None; st.rerun()
    
    s_cols = st.columns(3)
    for idx, s in enumerate(["Analyze Movers", "Strike Zones", "Market Trend"]):
        if s_cols[idx].button(s, key=f"s_btn_{idx}", use_container_width=True): 
            st.session_state["suggested_query"] = s

    for m in st.session_state["messages"]:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    chat_prompt = st.chat_input("Ask Terminal...")
    final_q = st.session_state.get("suggested_query") if st.session_state.get("suggested_query") else chat_prompt

    if final_q:
        st.session_state["messages"].append({"role": "user", "content": final_q})
        st.session_state["suggested_query"] = None
        with st.chat_message("user"): st.markdown(final_q)
        with st.chat_message("assistant"):
            with st.spinner("🧠 Processing..."):
                model = genai.GenerativeModel(get_working_model(api_key))
                ans = model.generate_content(f"Context: {st.session_state.current_context}\nQ: {final_q}").text
                st.markdown(ans); st.session_state["messages"].append({"role": "assistant", "content": ans})
        st.rerun()

with tab_a:
    st.write("### 📜 Sovereign Terminal Protocol (v79.0)")
    st.markdown("""
    The Sovereign Terminal is a professional-grade intelligence suite for tactical analysis.
    
    **🏛️ Data & Analysis Engine**
    * **Strike Zone Restored:** Intraday $S1$ (Entry) and $R1$ (Target) are now hard-coded into the Top 5 metric cards.
    * **Overstated Alert:** Leaders moving >4.0% are automatically tagged as 'OVERSTATED' to flag high-energy volatility.
    * **Strategic Search:** Manual ticker input triggers precision pivot math and AI bull thesis.
    
    **🏛️ UI/UX & Mobile Hardening**
    * **Adaptive Contrast:** High-contrast Light Mode on mobile bypasses browser 'Smart Inversion' bugs.
    * **Interaction Stability:** Key-anchored buttons and state-persistent logic prevent 'dead elements'.
    
    **🏛️ Technical Protocol**
    | Category | Implementation Detail |
    | :--- | :--- |
    | **Pivot Formula** | $P = (High + Low + Close) / 3$ |
    | **Support ($S1$)** | $(2 \\times P) - High$ |
    | **Resistance ($R1$)** | $(2 \\times P) - Low$ |
    | **Quota Cap** | 2,000 RPM (Professional Tier) |
    """)

st.markdown("""<div class="disclaimer-box">⚠️ RISK WARNING: Financial trading involves high risk. All decisions are the responsibility of the user.</div>""", unsafe_allow_html=True)
