import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. QUOTA-SHIELDED AI HANDLER ---
def handle_ai_query(prompt, context, key):
    genai.configure(api_key=key)
    # Shield: Forced 5-second pause to prevent rapid-fire requests
    time.sleep(5) 
    
    for attempt in range(3):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Shield: Shortened prompt to stay under token-per-minute limits
            compressed_prompt = f"Data: {context[:500]}\nQ: {prompt}"
            return model.generate_content(compressed_prompt).text
        except Exception as e:
            if "429" in str(e):
                # Shield: Aggressive 10-second wait on error
                time.sleep(10)
                continue
            return "⚠️ Service busy. Please wait 30s before trying again."

# --- 4. DATA ENGINE (Base v31.0 - Stable) ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    idx = 1 if "India" in exchange_choice else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        symbols = pd.read_html(response.text)[idx]['Symbol'].tolist()
        if idx == 1: symbols = [s + ".NS" for s in symbols]
        sample = symbols[::max(1, len(symbols)//40)] 
        results = []
        for symbol in sample:
            try:
                t = yf.Ticker(symbol); h = t.history(period="2d")
                if len(h) < 2: continue
                curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                results.append({
                    "ticker": symbol, "price": curr, "change": ((curr-prev)/prev)*100,
                    "entry": (2*piv)-hi, "target": (2*piv)-lo, "abs_change": abs(((curr-prev)/prev)*100)
                })
            except: continue
        return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')
    except: return []

# --- 5. MAIN UI ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical", "🤖 AI Desk", "📜 About"])

with tab_tactical:
    leaders = rank_movers(exchange_choice)
    curr_sym = "₹" if "India" in exchange_choice else "$"
    if leaders:
        leader_context = ""
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                st.metric(label=stock['ticker'], value=f"{curr_sym}{stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr_sym}{stock['entry']:.2f}</span><br><span class='val-target'>Target: {curr_sym}{stock['target']:.2f}</span></div>", unsafe_allow_html=True)
                leader_context += f"{stock['ticker']}:{stock['price']};"
        st.session_state.current_context = leader_context

with tab_research:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        if st.button("🗑️ Clear"): st.session_state.messages = []; st.rerun()
        
        # Shield: Suggestion buttons no longer auto-trigger a request
        suggestions = ["Analyze the tape", "Define Strike Zone"]
        cols = st.columns(2)
        clicked = None
        for i, s in enumerate(suggestions):
            if cols[i].button(s): clicked = s

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        if (prompt := st.chat_input("Ask a question...")) or clicked:
            final_p = prompt if prompt else clicked
            st.session_state.messages.append({"role": "user", "content": final_p})
            with st.chat_message("user"): st.write(final_p)
            with st.chat_message("assistant"):
                ans = handle_ai_query(final_p, st.session_state.current_context, api_key)
                st.write(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. Trading involves risk. You are solely responsible for your financial decisions.</div>""", unsafe_allow_html=True)
