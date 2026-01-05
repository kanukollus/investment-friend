import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# --- 1. ARCHITECTURAL CONFIG & HARD-LOCKED UX ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* 1. Global Nuclear Reset to Pure White */
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
    
    /* 2. Neubrutalist Title Lock */
    .ux-title {
        color: #000000 !important;
        font-size: 2.5rem !important;
        font-weight: 950 !important;
        -webkit-text-stroke: 1px #000;
        margin-bottom: 10px;
    }

    /* 3. Global Text Hard-Lock */
    div[data-testid="stWidgetLabel"] p, label p, button[data-baseweb="tab"] p, .stMarkdown p { 
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        font-weight: 800 !important;
    }

    /* 4. Strategic Search: Neubrutalist Input */
    div[data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 4px solid #000000 !important;
        border-radius: 0px !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 900 !important;
        box-shadow: 6px 6px 0px #000000 !important;
    }

    /* 5. Neubrutalist Buttons (AI & Reset) */
    div[data-testid="stButton"] button {
        background-color: #FFD700 !important; /* Gold for AI Suggestions */
        color: #000000 !important;
        border: 3px solid #000000 !important;
        border-radius: 0px !important;
        font-weight: 900 !important;
        box-shadow: 4px 4px 0px #000000 !important;
        width: 100% !important;
    }
    /* Reset Button Specific Color */
    .reset-btn div[data-testid="stButton"] button {
        background-color: #FF4B4B !important; /* Institutional Red */
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 6. Tactical & AI Response Containers */
    .response-card {
        background-color: #FFFFFF;
        border: 4px solid #000000;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 8px 8px 0px #000000;
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. REINFORCED STATE LAYER ---
for key in ["messages", "current_context", "suggested_query", "active_tab", "search_ticker"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else None
if st.session_state.active_tab is None: st.session_state.active_tab = 0

# --- 3. DATA & AI ENGINE ---
@st.cache_data(ttl=600)
def get_movers(universe):
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

# --- 4. MAIN UI ---
st.markdown('<div class="ux-title">🏛️ SOVEREIGN TERMINAL</div>', unsafe_allow_html=True)

exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_t, tab_r, tab_p = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    st.session_state.active_tab = 0
    leaders = get_movers(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        for s in leaders:
            st.markdown(f"""
            <div class="response-card">
                <div style="font-size:1.4rem; font-weight:950;">{s['ticker']}</div>
                <div style="font-size:2rem; font-weight:900;">{curr}{s['price']:.2f} 
                    <span style="color:#1D8139;">({s['change']:.2f}%)</span>
                </div>
                <div style="background:#000; color:#FFF; padding:10px; margin-top:10px; font-weight:bold;">
                    ENTRY: {curr}{s['entry']:.2f} | TARGET: {curr}{s['target']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    # SEARCH BAR: Anchored to session state
    search_q = st.text_input("Strategic Search (Ticker):", key=f"neu_src_{exch}").strip().upper()
    if search_q:
        try:
            q_t = yf.Ticker(search_q); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p_c, prev_c, p_h, p_l = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                p_pt = (p_h + p_l + prev_c) / 3
                st.markdown(f"""
                <div class="response-card" style="border-color:#58a6ff;">
                    <div style="font-size:1.8rem; font-weight:950;">SEARCH: {search_q}</div>
                    <div style="background:#000; color:#FFF; padding:10px; margin-top:10px;">
                        ENTRY: {curr}{(2*p_pt)-p_h:.2f} | TARGET: {curr}{(2*p_pt)-p_l:.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except: st.error("Ticker Feed Error.")

with tab_r:
    st.session_state.active_tab = 1
    # 🏛️ GLOBAL RESET: Always visible at the top of Research
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("🗑️ RESET TERMINAL CHAT", key="global_reset"):
        st.session_state.messages = []; st.session_state.suggested_query = None; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # AI SUGGESTIONS
    s_cols = st.columns(3)
    for idx, s in enumerate(["Analyze Movers", "Strike Zones", "Market Trend"]):
        if s_cols[idx].button(s, key=f"neu_btn_{idx}"): st.session_state.suggested_query = s

    # RESPONSE RENDERER: Forced high-contrast
    for m in st.session_state.messages:
        role_color = "#000" if m["role"] == "user" else "#58a6ff"
        st.markdown(f"""
        <div class="response-card" style="border-left:10px solid {role_color};">
            <b style="color:{role_color}; text-transform:uppercase;">{m['role']}:</b><br>{m['content']}
        </div>
        """, unsafe_allow_html=True)
    
    chat_input = st.chat_input("Ask Terminal...")
    final_q = st.session_state.get("suggested_query") if st.session_state.get("suggested_query") else chat_input

    if final_q:
        st.session_state.messages.append({"role": "user", "content": final_q})
        st.session_state.suggested_query = None
        # AI Processing Logic would execute here
        st.rerun()

with tab_p:
    st.session_state.active_tab = 2
    st.write("### 📜 Sovereign Protocol (v88.0)")
    st.markdown("""
    * **Interaction Anchoring:** Reset Chat is now a global red Neubrutalist button pinned to the Research Desk.
    * **Search Persistence:** Ticker search results are wrapped in high-contrast blue frames to bypass browser ghosting.
    * **State Recovery:** `AttributeError` guard fully implemented to handle rapid clicks on mobile.
    """)
