import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# --- 1. ARCHITECTURAL CONFIG & THEME HARD-LOCK ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

# CSS: Nuclear Reset
st.markdown("""
    <style>
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    
    /* Force Light Theme Base */
    .stApp { background-color: #FFFFFF !important; }

    /* HARD-LOCK: Radio & Tab Labels (Resolves IMG_3195, 3197) */
    div[data-testid="stWidgetLabel"] p, label p, button[data-baseweb="tab"] p { 
        color: #000000 !important; 
        font-weight: 900 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* HARD-LOCK: Search Bar Input (Resolves IMG_3196, 3201) */
    div[data-testid="stTextInput"] input {
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: bold !important;
    }

    /* Tactical Card Container */
    .tactical-card {
        background-color: #FFFFFF;
        border: 2px solid #E6E9EF;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if "current_context" not in st.session_state: st.session_state["current_context"] = ""

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=600)
def get_market_data(universe):
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
st.title("🏛️ Sovereign Terminal")

# Universe Control - Using Inline Labels
exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_t, tab_r, tab_a = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    leaders = get_market_data(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        for s in leaders:
            # NUCLEAR FIX: Forced Inline Styles for Ticker and Price
            st.markdown(f"""
            <div class="tactical-card">
                <div style="color: #000000 !important; font-size: 1.2rem; font-weight: 900; margin-bottom: 4px;">
                    {s['ticker']} {'🔥 OVERSTATED' if abs(s['change']) > 4.0 else ''}
                </div>
                <div style="color: #000000 !important; font-size: 1.8rem; font-weight: 800; margin-bottom: 8px;">
                    {curr}{s['price']:.2f} 
                    <span style="color: {'#1D8139' if s['change'] > 0 else '#D32F2F'}; font-size: 1.1rem; font-weight: 700;">
                        ({s['change']:.2f}%)
                    </span>
                </div>
                <div style="background-color: #F1F3F5; border-radius: 8px; padding: 12px; color: #000000 !important; font-weight: 700; border: 1px solid #E6E9EF;">
                    Entry: {curr}{s['entry']:.2f} | Target: {curr}{s['target']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.session_state["current_context"] = str(leaders)
    
    st.divider()
    search = st.text_input("Strategic Search (Ticker):", key=f"src_{exch}").strip().upper()

with tab_r:
    # HARD-CONTRAST CHAT MESSAGES
    for m in st.session_state["messages"]:
        bg = "#F8F9FA" if m["role"] == "assistant" else "#FFFFFF"
        border = "#005CC5" if m["role"] == "assistant" else "#000000"
        st.markdown(f"""
        <div style="background-color: {bg}; border-left: 5px solid {border}; padding: 16px; margin-bottom: 12px; color: #000000 !important; font-size: 1rem;">
            <b style="color: {border};">{m['role'].upper()}:</b> {m['content']}
        </div>
        """, unsafe_allow_html=True)
    
    if prompt := st.chat_input("Ask Terminal..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        # AI logic would process here...
        st.rerun()

with tab_a:
    st.write("### 📜 Sovereign Protocol (v85.0)")
    st.markdown("""
    **🏛️ Critical Visibility Fixes**
    * **Ticker Hard-Lock:** Tickers and prices are now rendered with inline `color: #000000 !important` to stop the white-on-white bug.
    * **Input Hard-Lock:** Search bar background and text colors are forced to high-contrast blue/black.
    * **Chat Hard-Lock:** AI responses use standard HTML `div` containers to prevent browser "ghosting".
    """)
