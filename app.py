import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# --- 1. ARCHITECTURAL CONFIG & NEUBRUTALIST ENGINE ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* 1. Global Reset: Forced Institutional White */
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
    
    /* 2. Neubrutalist Header (Resolves Ghosting in IMG_3202) */
    .ux-main-title {
        color: #000000 !important;
        font-size: 2.8rem !important;
        font-weight: 950 !important;
        line-height: 1.1;
        margin-bottom: 20px;
        text-transform: uppercase;
        -webkit-text-stroke: 1px #000;
    }

    /* 3. Universe & Tab Hard-Lock (Resolves IMG_3203/3204) */
    div[data-testid="stWidgetLabel"] p, label p, button[data-baseweb="tab"] p { 
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        font-weight: 900 !important;
        font-size: 1.2rem !important;
    }

    /* 4. Strategic Search: High-Visibility Block (Resolves IMG_3201) */
    div[data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 3px solid #000000 !important;
        border-radius: 0px !important; /* Brutalist sharp edges */
        -webkit-text-fill-color: #000000 !important;
        font-weight: 800 !important;
        box-shadow: 4px 4px 0px #000000 !important;
    }

    /* 5. AI Suggestions: Neubrutalist Action Buttons */
    div[data-testid="stButton"] button {
        background-color: #FFD700 !important; /* High-Visibility Gold */
        color: #000000 !important;
        border: 3px solid #000000 !important;
        border-radius: 0px !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        box-shadow: 4px 4px 0px #000000 !important;
        width: 100% !important;
        margin-bottom: 10px;
    }

    /* 6. Tactical Cards: High-Contrast Containers */
    .tactical-card {
        background-color: #FFFFFF;
        border: 3px solid #000000;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 8px 8px 0px #000000;
    }
    .card-ticker { color: #000000 !important; font-size: 1.5rem; font-weight: 900; }
    .card-price { color: #000000 !important; font-size: 2.5rem; font-weight: 950; }
    .card-zone { 
        background-color: #000000; color: #FFFFFF !important; 
        padding: 10px; margin-top: 10px; font-weight: 800; font-family: monospace; 
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if "current_context" not in st.session_state: st.session_state["current_context"] = ""
if "suggested_query" not in st.session_state: st.session_state["suggested_query"] = None

# --- 3. DATA & AI ENGINES ---
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

# --- 4. MAIN INTERFACE ---
st.markdown('<div class="ux-main-title">🏛️ Sovereign<br>Terminal</div>', unsafe_allow_html=True)

exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_t, tab_r, tab_p = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    leaders = get_movers(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        for s in leaders:
            st.markdown(f"""
            <div class="tactical-card">
                <div class="card-ticker">{s['ticker']} {'🔥 OVERSTATED' if abs(s['change']) > 4.0 else ''}</div>
                <div class="card-price">{curr}{s['price']:.2f} <span style="color:#1D8139; font-size:1.2rem;">({s['change']:.2f}%)</span></div>
                <div class="card-zone">ENTRY: {curr}{s['entry']:.2f} | TARGET: {curr}{s['target']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    search = st.text_input("Strategic Search (Ticker):", key=f"neu_src_{exch}").strip().upper()

with tab_r:
    # 🏛️ AI SUGGESTIONS: NEUBRUTALIST STYLE
    s_cols = st.columns(3)
    s_list = ["Analyze Movers", "Strike Zones", "Market Trend"]
    for idx, s in enumerate(s_list):
        if s_cols[idx].button(s, key=f"neu_btn_{idx}"): st.session_state["suggested_query"] = s

    for m in st.session_state["messages"]:
        bg = "#F0F2F6" if m["role"] == "assistant" else "#FFFFFF"
        st.markdown(f"<div style='background:{bg}; border:3px solid #000; padding:15px; margin-bottom:10px; color:#000; font-weight:800;'><b>{m['role'].upper()}:</b> {m['content']}</div>", unsafe_allow_html=True)
    
    if prompt := st.chat_input("Ask Terminal..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        st.rerun()

with tab_p:
    st.markdown("<h3 style='color:#000; font-weight:900;'>📜 Sovereign Protocol (v87.0)</h3>", unsafe_allow_html=True)
    st.markdown("""
    * **Ghosting Elimination:** Replaced standard headers with high-stroke Neubrutalist titles.
    * **AI Suggestion Lock:** Buttons updated to High-Visibility Gold with 3px black strokes to prevent invisibility.
    * **Contrast Integrity:** All containers use hardware-level white backgrounds with solid black typography.
    """)
