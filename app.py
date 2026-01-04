import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Intelligence Terminal", layout="wide")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. DYNAMIC AI HANDLER (Vedic-Stability Logic) ---
def get_working_model(key):
    genai.configure(api_key=key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash' # Higher RPM for 2026 free tier
        return available[0]
    except: return "models/gemini-1.5-flash"

def handle_ai_query(prompt, context, key):
    for attempt in range(3):
        try:
            model = genai.GenerativeModel(get_working_model(key))
            full_prompt = f"System Context: {context}\n\nUser Question: {prompt}"
            time.sleep(random.uniform(1.5, 3.0)) # Pro-active throttling to stay under free tier RPM
            return model.generate_content(full_prompt).text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep((attempt + 1) * 3) # Exponential Backoff
                continue
            return "⚠️ Service Busy: Gemini quota reached (15 RPM). Please wait 60s."

# --- 4. MULTI-EXCHANGE ENGINE ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    # Select Source based on Exchange Choice
    if exchange_choice == "India (Nifty 50)":
        url = "https://en.wikipedia.org/wiki/NIFTY_50"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        # Nifty 50 symbols require .NS suffix for Yahoo Finance
        symbols = [s + ".NS" for s in pd.read_html(response.text)[1]['Symbol'].tolist()]
    else:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        symbols = pd.read_html(response.text)[0]['Symbol'].tolist()
    
    # Stratified global scan to find real volatility
    sample = symbols[::max(1, len(symbols)//60)] 
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

# --- 5. MAIN INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")

# EXCHANGE SELECTOR - Anchored at the top for easy access
exchange_choice = st.radio("Select Trading Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk"])

with tab_tactical:
    st.write(f"### {exchange_choice} Momentum Leaders")
    leaders = rank_movers(exchange_choice)
    leader_context = f"Leaders in {exchange_choice}: "
    
    cols = st.columns(5)
    for i, stock in enumerate(leaders):
        with cols[i]:
            status = "⚠️ OVEREXTENDED" if stock['price'] > stock['target'] else "✅ STRIKE ZONE"
            st.metric(label=stock['ticker'], value=f"{'₹' if 'India' in exchange_choice else '$'}{stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""<div class="strike-zone-card"><b style="color:#8b949e; font-size:0.7rem;">{status}</b><br><span class="val-entry">Entry: {stock['entry']:.2f}</span><br><span class="val-target">Target: {stock['target']:.2f}</span></div>""", unsafe_allow_html=True)
            leader_context += f"{stock['ticker']} ({stock['price']:.2f}); "

    st.divider()
    st.write("### 🔍 Strategic Asset Search")
    query = st.text_input("Enter Ticker (For India, add .NS - e.g. RELIANCE.NS, NVDA, BTC-USD):").upper()
    if query:
        try:
            q_t = yf.Ticker(query); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                e, t = (2*piv)-hi, (2*piv)-lo
                st.metric(label=query, value=f"{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"<div class='strike-zone-card'>Entry: ${e:.2f} | Target: ${t:.2f}</div>", unsafe_allow_html=True)
                st.session_state.current_context = f"Analyzing {query}: {p:.2f}. " + leader_context
        except: st.error("Ticker not found.")
    else: st.session_state.current_context = leader_context

with tab_research:
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear"):
            st.session_state.messages = []; st.rerun()

    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        # Suggestions Restored
        suggestions = ["Explain the flush", "Define Strike Zone", "Analyze leaders"]
        s_cols = st.columns(3); clicked = None
        for idx, s in enumerate(suggestions):
            if s_cols[idx].button(s, use_container_width=True): clicked = s

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        prompt = st.chat_input("Analyze the tape...")
        final_query = prompt if prompt else clicked

        if final_query:
            st.session_state.messages.append({"role": "user", "content": final_query})
            with st.chat_message("user"): st.write(final_query)
            with st.chat_message("assistant"):
                with st.spinner("Reviewing market energy..."):
                    context = "Role: Senior Institutional Advisor. Context: " + st.session_state.current_context
                    answer = handle_ai_query(final_query, context, api_key)
                    st.markdown(f"<div class='advisor-brief'>{answer}</div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
