import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai

# --- 1. ARCHITECTURAL LOCK: INSTITUTIONAL CONTRAST ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* Global Reset to Pure White */
    header, [data-testid="stToolbar"] { visibility: hidden !important; height: 0 !important; }
    .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
    
    /* Institutional Labels: Forced Black */
    div[data-testid="stWidgetLabel"] p, label p, button[data-baseweb="tab"] p { 
        color: #000000 !important; font-weight: 800 !important; -webkit-text-fill-color: #000000 !important;
    }

    /* FIX: Search Box Persistence (No Shadow to prevent layering bugs) */
    div[data-testid="stTextInput"] input {
        background-color: #F8F9FA !important; color: #000 !important; border: 2px solid #000 !important;
        font-weight: 700 !important; -webkit-text-fill-color: #000 !important;
    }

    /* Action Buttons: High-Visibility Signal */
    div[data-testid="stButton"] button {
        background-color: #FFD700 !important; color: #000 !important; border: 2px solid #000 !important;
        font-weight: 800 !important; width: 100% !important;
    }

    /* Executive Intel Frames */
    .intel-frame {
        background-color: #FFFFFF; border: 2px solid #000; padding: 15px;
        margin-bottom: 15px; color: #000 !important;
    }
    .badge-overstated { background: #FF4B4B; color: #FFF; padding: 3px 8px; font-weight: 900; }
    .badge-volatile { background: #000; color: #FFF; padding: 3px 8px; font-weight: 900; }
    </style>
""", unsafe_allow_html=True)

# --- 2. PERSISTENT STATE VAULT ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. DATA & INTELLIGENCE ENGINE ---
@st.cache_data(ttl=300)
def fetch_terminal_data(universe):
    """Calculates Strike Zones & Overstated Logic"""
    idx = 1 if "India" in universe else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        syms = pd.read_html(url)[idx]['Symbol'].tolist()
        if idx == 1: syms = [s + ".NS" for s in syms]
        res = []
        for s in syms[::max(1, len(syms)//40)]:
            t = yf.Ticker(s); h = t.history(period="2d")
            if len(h) < 2: continue
            c, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
            p = (hi + lo + prev) / 3
            res.append({"ticker": s, "price": c, "change": ((c-prev)/prev)*100, "entry": (2*p)-hi, "target": (2*p)-lo, "abs": abs(((c-prev)/prev)*100)})
        return pd.DataFrame(res).sort_values(by='abs', ascending=False).head(5).to_dict('records')
    except: return []

# --- 4. MAIN INTERFACE ---
st.markdown("<h2 style='color:#000; font-weight:900;'>🏛️ Sovereign Terminal</h2>", unsafe_allow_html=True)
exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_t, tab_r, tab_p = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    leaders = fetch_terminal_data(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        leader_ctx = ""
        for s in leaders:
            is_over = abs(s['change']) > 4.0
            badge = f'<span class="badge-overstated">🔥 OVERSTATED</span>' if is_over else f'<span class="badge-volatile">⚡ VOLATILE</span>'
            st.markdown(f"""
            <div class="intel-frame">
                {badge}
                <div style="font-size:1.3rem; font-weight:800; margin-top:5px;">{s['ticker']}</div>
                <div style="font-size:2rem; font-weight:900;">{curr}{s['price']:.2f} <span style="color:{'#28a745' if s['change'] > 0 else '#dc3545'};">({s['change']:.2f}%)</span></div>
                <div style="background:#F1F3F5; padding:8px; margin-top:8px; font-weight:700;">ENTRY: {curr}{s['entry']:.2f} | TARGET: {curr}{s['target']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            leader_ctx += f"{s['ticker']}:{s['price']} ({'Overstated' if is_over else 'Volatile'}); "
        st.session_state.current_context = leader_ctx
    
    st.divider()
    search = st.text_input("Strategic Search (Ticker):", key=f"src_93_{exch}").strip().upper()
    if search:
        q_t = yf.Ticker(search); q_h = q_t.history(period="2d")
        if not q_h.empty:
            p_c, prev_c, p_h, p_l = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
            p_pt = (p_h + p_l + prev_c) / 3
            st.markdown(f"""
            <div class="intel-frame" style="border-color:#005CC5;">
                <div style="font-weight:900;">SEARCH: {search}</div>
                <div style="font-size:1.5rem; font-weight:900;">{curr}{p_c:.2f}</div>
                <div style="background:#000; color:#FFF; padding:10px; margin-top:5px; font-weight:800;">ENTRY: {curr}{(2*p_pt)-p_h:.2f} | TARGET: {curr}{(2*p_pt)-p_l:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

with tab_r:
    # Always-Visible Action Row
    c1, c2, c3 = st.columns(3)
    if c1.button("🗑️ RESET"): st.session_state.messages = []; st.rerun()
    if c2.button("📈 MOVERS"): sq = "Analyze Movers"
    else: sq = None
    if c3.button("🎯 ZONES"): sq = "Strike Zones"
    
    # Render History
    for m in st.session_state.messages:
        role_label = "USER" if m["role"] == "user" else "ASSISTANT"
        st.markdown(f'<div class="intel-frame" style="border-left:8px solid #FFD700;"><b>{role_label}:</b><br>{m["content"]}</div>', unsafe_allow_html=True)

    chat_input = st.chat_input("Ask Terminal...")
    final_q = sq if sq else chat_input

    if final_q:
        st.session_state.messages.append({"role": "user", "content": final_q})
        with st.spinner("🧠 GENERATING INTELLIGENCE..."):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-1.5-flash')
                ans = model.generate_content(f"Market Context: {st.session_state.current_context}\nQuestion: {final_q}")
                st.session_state.messages.append({"role": "assistant", "content": ans.text})
            except:
                st.session_state.messages.append({"role": "assistant", "content": "Critical Feed Interruption. Please check API Credits."})
        st.rerun()

with tab_p:
    st.markdown("### 📜 Sovereign Protocol (v93.0)")
    st.markdown("""
    * **Layer Integrity:** Removed heavy Neubrutalist shadows to resolve widget layering collisions.
    * **Logic Restoration:** Hard-coded the Strike Zone ($S1/R1$) and Overstated flags into every market card.
    * **Synchronous Buffering:** AI responses are forced into the session state before the screen refresh.
    """)
