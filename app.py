import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time

# --- 1. SENIOR UX: REINFORCED STRUCTURAL GRID ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    .stApp { background-color: #FFFFFF !important; color: #000 !important; }
    
    /* 1. LAYER FIX: Absolute Priority */
    div[data-testid="stTextInput"], div[data-testid="stButton"], .stChatInput {
        z-index: 1000 !important;
        position: relative !important;
    }

    /* 2. NEUBRUTALIST INPUTS */
    div[data-testid="stTextInput"] input {
        background-color: #FFFFFF !important; color: #000 !important; border: 4px solid #000 !important;
        font-weight: 900 !important; box-shadow: 6px 6px 0px #000 !important; border-radius: 0px !important;
    }

    /* 3. INTEL FRAMES: Hard-Coded Response Borders */
    .intel-frame {
        background-color: #FFFFFF; border: 4px solid #000; padding: 20px;
        margin-bottom: 20px; box-shadow: 8px 8px 0px #FFD700; color: #000 !important;
    }
    
    /* 4. TABS & LABELS */
    button[data-baseweb="tab"] p { color: #000 !important; font-weight: 900 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE REINFORCEMENT ---
for k, v in {"messages": [], "current_context": "", "suggested_query": None}.items():
    if k not in st.session_state: st.session_state[k] = v

# --- 3. DATA & AI ENGINES ---
@st.cache_data(ttl=600)
def get_market_intelligence(universe):
    """Calculates Strike Zones & Volatility Tags"""
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

# --- 4. INTERFACE ---
st.markdown("<h1 style='color:#000; font-weight:950;'>🏛️ SOVEREIGN TERMINAL</h1>", unsafe_allow_html=True)
exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_t, tab_r, tab_p = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    leaders = get_market_intelligence(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        leader_ctx = ""
        for s in leaders:
            tag = "🔥 OVERSTATED" if abs(s['change']) > 4.0 else "⚡ VOLATILE"
            st.markdown(f"""
            <div class="intel-frame">
                <div style="background:#000; color:#FFF; padding:5px 10px; font-weight:900; display:inline-block;">{tag}</div>
                <div style="font-size:1.5rem; font-weight:950; margin-top:10px; color:#000;">{s['ticker']}</div>
                <div style="font-size:2.2rem; font-weight:900; color:#000;">{curr}{s['price']:.2f} <span style="color:{'#1D8139' if s['change'] > 0 else '#D32F2F'};">({s['change']:.2f}%)</span></div>
                <div style="background:#000; color:#FFF; padding:12px; margin-top:10px; font-weight:900; font-family:monospace;">ENTRY: {curr}{s['entry']:.2f} | TARGET: {curr}{s['target']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            leader_ctx += f"{s['ticker']}:{s['price']}; "
        st.session_state.current_context = leader_ctx
    
    st.divider()
    search_input = st.text_input("Strategic Search (Ticker):", key=f"src_92_{exch}").strip().upper()
    if search_input:
        try:
            q_t = yf.Ticker(search_input); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p_c, prev_c, p_h, p_l = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                p_pt = (p_h + p_l + prev_c) / 3
                st.markdown(f"""
                <div class="intel-frame" style="border-color:#58a6ff;">
                    <div style="font-size:1.8rem; font-weight:950; color:#000;">SEARCH: {search_input}</div>
                    <div style="background:#000; color:#FFF; padding:12px; margin-top:10px; font-weight:900;">
                        ENTRY: {curr}{(2*p_pt)-p_h:.2f} | TARGET: {curr}{(2*p_pt)-p_l:.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except: st.error("Search Feed Error.")

with tab_r:
    # 🏛️ INTERACTION BLOCK
    if st.button("🗑️ RESET CHAT", key="res_92"):
        st.session_state.messages = []; st.rerun()
    
    s_cols = st.columns(3)
    for idx, s in enumerate(["Analyze Movers", "Strike Zones", "Market Trend"]):
        if s_cols[idx].button(s, key=f"btn_92_{idx}"):
            st.session_state.suggested_query = s

    # 🏛️ PERSISTENT RENDERER
    for m in st.session_state.messages:
        border = "#000" if m["role"] == "user" else "#FFD700"
        st.markdown(f'<div class="intel-frame" style="border-left:12px solid {border};"><b>{m["role"].upper()}:</b><br>{m["content"]}</div>', unsafe_allow_html=True)

    # 🏛️ RESPONSE VAULT LOGIC
    chat_prompt = st.chat_input("Ask Terminal...")
    final_q = st.session_state.get("suggested_query") if st.session_state.get("suggested_query") else chat_prompt

    if final_q:
        api_key = st.secrets.get("GEMINI_API_KEY")
        st.session_state.messages.append({"role": "user", "content": final_q})
        st.session_state.suggested_query = None # Clear immediately to prevent loop
        
        with st.spinner("🧠 AI HEARTBEAT: Generating Strategic Intelligence..."):
            try:
                # 🏛️ BUFFERING: AI writes to state before rerun
                model = genai.GenerativeModel('gemini-1.5-flash')
                gen_ai = model.generate_content(f"Context: {st.session_state.current_context}\nQ: {final_q}")
                st.session_state.messages.append({"role": "assistant", "content": gen_ai.text})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": "Analysis Feed Offline."})
        st.rerun() # Flush Buffer to Screen

with tab_p:
    st.write("### 📜 Sovereign Protocol (v92.0)")
    st.markdown("""
    * **Response Buffering:** AI output is now saved to the session state *before* the page refresh to prevent 'user-only' text ghosting.
    * **Search persistence:** Search results are wrapped in high-priority layers to prevent vanishing during tactical updates.
    * **Tactical Integrity:** Maintained 'Overstated' labels and 'Strike Zone' pivot calculations.
    """)
