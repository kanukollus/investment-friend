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
    
    /* MOBILE-ONLY HARD RESET (< 768px) */
    @media (max-width: 768px) {
        .stApp { background-color: #FFFFFF !important; }
        
        /* Hard-lock all standard labels to deep charcoal */
        div[data-testid="stWidgetLabel"] p, label p { 
            color: #1a1a1a !important; 
            -webkit-text-fill-color: #1a1a1a !important;
            font-weight: 800 !important;
        }

        /* Fix the Strategic Search "Blackout" */
        div[data-testid="stTextInput"] input {
            color: #1a1a1a !important;
            background-color: #f0f2f6 !important;
            border: 1px solid #1a1a1a !important;
            -webkit-text-fill-color: #1a1a1a !important;
        }

        /* Fix invisible metrics (Tickers/Prices) */
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: #1a1a1a !important;
            -webkit-text-fill-color: #1a1a1a !important;
        }
    }

    /* Professional Card Styling */
    .tactical-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .ticker-header { color: #1a1a1a; font-size: 1.2rem; font-weight: 900; }
    .price-sub { color: #222222; font-size: 1.5rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL STATE ---
if "messages" not in st.session_state: st.session_state["messages"] = []
if "current_context" not in st.session_state: st.session_state["current_context"] = ""

# --- 3. DATA ENGINE ---
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
exch = st.radio("Universe Selection:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_t, tab_r, tab_a = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    leaders = rank_movers(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        for s in leaders:
            # NUCLEAR FIX: Using custom HTML for ticker and price to bypass invisibility
            st.markdown(f"""
            <div class="tactical-card">
                <div class="ticker-header">{s['ticker']} {'🔥 OVERSTATED' if abs(s['change']) > 4.0 else ''}</div>
                <div class="price-sub">{curr}{s['price']:.2f} <span style="color:{'#28a745' if s['change'] > 0 else '#dc3545'}; font-size:1rem;">({s['change']:.2f}%)</span></div>
                <div style="background:#eeeeee; padding:8px; border-radius:5px; margin-top:10px; font-weight:bold; color:#1a1a1a;">
                    Entry: {curr}{s['entry']:.2f} | Target: {curr}{s['target']:.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    search = st.text_input("Strategic Search (Ticker):", key=f"search_{exch}").strip().upper()

with tab_r:
    for m in st.session_state["messages"]:
        # Custom HTML Chat bubbles for 100% visibility
        color = "#1a1a1a" if m["role"] == "user" else "#005cc5"
        st.markdown(f"<div style='background:#f0f2f6; border-left:5px solid {color}; padding:15px; margin-bottom:10px; color:#1a1a1a;'><b>{m['role'].upper()}:</b> {m['content']}</div>", unsafe_allow_html=True)
    
    if prompt := st.chat_input("Ask Terminal..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        # [Simulated AI Call logic continues here...]
        st.rerun()

with tab_a:
    st.write("### 📜 Sovereign Protocol (v83.0)")
    st.markdown("* **Invisibility Shield:** Replaced standard metrics with Hard-Coded HTML to prevent white-on-white text bugs.\n* **Search Recovery:** Fixed the CSS 'Blackout' on the strategic search input.")
