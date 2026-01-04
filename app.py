import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# --- 1. ARCHITECTURAL CONFIG & EXTREME CONTRAST THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* 1. Global UI Stealth */
    header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; height: 0 !important; }
    
    /* 2. Desktop Mode (Dark) */
    .stApp { background-color: #0d1117; color: #FFFFFF; }
    
    /* 3. MOBILE-ONLY "PAPER-WHITE" MODE (< 768px) */
    @media (max-width: 768px) {
        /* Force Solid White Background */
        .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
        
        /* Force Universe/Radio Labels to Solid Black */
        div[data-testid="stWidgetLabel"] p, div[data-testid="stRadio"] label { 
            color: #000000 !important; 
            font-weight: 900 !important; 
            font-size: 1.1rem !important;
            -webkit-text-fill-color: #000000 !important;
        }

        /* Force Tab Menu (Research Desk, Protocol) to Solid Black */
        button[data-baseweb="tab"] { 
            color: #444444 !important; 
            font-weight: 700 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] { 
            color: #000000 !important; 
            border-bottom-color: #000000 !important; 
        }

        /* Force Metric Values to Solid Black */
        div[data-testid="stMetricValue"] { 
            color: #000000 !important; 
            -webkit-text-fill-color: #000000 !important; 
            font-weight: 800 !important; 
        }

        /* Force AI Response Visibility */
        [data-testid="stChatMessage"] { 
            background-color: #f0f2f6 !important; 
            border: 2px solid #000000 !important; 
        }
        [data-testid="stChatMessage"] p { 
            color: #000000 !important; 
            -webkit-text-fill-color: #000000 !important; 
            font-weight: 500 !important;
        }
    }

    /* Standard Card Styling */
    .strike-zone-box { 
        background-color: #1f2937; 
        border: 1px solid #4b5563; 
        padding: 12px; 
        border-radius: 8px; 
        margin-top: 8px; 
        font-family: monospace; 
    }
    
    @media (max-width: 768px) {
        .strike-zone-box { background-color: #eeeeee !important; border-color: #000000 !important; color: #000000 !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE GUARD ---
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
st.title("🏛️ Sovereign Terminal")

# UNIVERSAL SELECTION LOCK
exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)
leaders = rank_movers(exch)

tab_t, tab_r, tab_a = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    curr = "₹" if "India" in exch else "$"
    if leaders:
        leader_ctx = ""
        for i, s in enumerate(leaders):
            status = "🔥 OVERSTATED" if abs(s['change']) > 4.0 else "⚡ VOLATILE"
            st.metric(label=f"{s['ticker']} ({status})", value=f"{curr}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
            st.markdown(f"<div class='strike-zone-box'><b>Entry: {curr}{s['entry']:.2f} | Target: {curr}{s['target']:.2f}</b></div>", unsafe_allow_html=True)
            leader_ctx += f"{s['ticker']}:{s['price']}; "
        st.session_state["current_context"] = leader_ctx

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
            with st.spinner("🧠 Thinking..."):
                model = genai.GenerativeModel(get_working_model(api_key))
                ans = model.generate_content(f"Context: {st.session_state.current_context}\nQ: {final_q}").text
                st.markdown(ans); st.session_state["messages"].append({"role": "assistant", "content": ans})
        st.rerun()

with tab_a:
    st.write("### 📜 Sovereign Protocol (v81.0)")
    st.markdown("""
    **🏛️ Mobile Visibility Guard**
    * **Paper-White Mode:** Forced white background/black text for mobile to ensure 100% legibility.
    * **Menu Anchor:** Universe selection and tab labels (Research Desk, Protocol) are hard-locked to bold black.
    * **Response Lock:** AI chat bubbles use hardware-level color fill to prevent invisible text bugs.
    """)
