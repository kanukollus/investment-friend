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
    .val-range { color: #8b949e; font-size: 0.75rem; font-family: monospace; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. DYNAMIC AI HANDLER (Stability Optimized) ---
def get_working_model(key):
    genai.configure(api_key=key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash'
        return available[0]
    except: return "models/gemini-1.5-flash"

def handle_ai_query(prompt, context, key):
    for attempt in range(3):
        try:
            model = genai.GenerativeModel(get_working_model(key))
            full_prompt = f"System Context: {context}\n\nUser Question: {prompt}"
            time.sleep(random.uniform(1.5, 3.0)) 
            return model.generate_content(full_prompt).text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep((attempt + 1) * 3)
                continue
            return "⚠️ Quota Exceeded. Please wait 60s for the reset."

# --- 4. DATA ENGINE (With KeyError Guard) ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    if exchange_choice == "India (Nifty 50)":
        url = "https://en.wikipedia.org/wiki/NIFTY_50"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        symbols = [s + ".NS" for s in pd.read_html(response.text)[1]['Symbol'].tolist()]
    else:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        symbols = pd.read_html(response.text)[0]['Symbol'].tolist()
    
    sample = symbols[::max(1, len(symbols)//60)] 
    results = []
    for symbol in sample:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) < 2: continue
            info = t.info
            curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
            piv = (hi + lo + prev) / 3
            results.append({
                "ticker": symbol, "name": info.get('longName', symbol), 
                "price": curr, "change": ((curr-prev)/prev)*100,
                "entry": (2*piv)-hi, "target": (2*piv)-lo,
                "h52": info.get('fiftyTwoWeekHigh', 0), "l52": info.get('fiftyTwoWeekLow', 0),
                "abs_change": abs(((curr-prev)/prev)*100)
            })
        except: continue
    
    # ⚠️ KEYERROR GUARD: Return empty list if no data was found
    if not results: return []
    
    df = pd.DataFrame(results)
    return df.sort_values(by='abs_change', ascending=False).head(5).to_dict('records')

# --- 5. UI INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Exchange Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk"])

with tab_tactical:
    st.write(f"### {exchange_choice} Volatility Leaders")
    leaders = rank_movers(exchange_choice)
    
    if not leaders:
        st.warning("No market data available for current sample. Refreshing in 60s...")
    else:
        leader_context = f"Leaders in {exchange_choice}: "
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                status = "⚠️ OVEREXTENDED" if stock['price'] > stock['target'] else "✅ STRIKE ZONE"
                curr_sym = "₹" if "India" in exchange_choice else "$"
                st.metric(label=stock['ticker'], value=f"{curr_sym}{stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
                
                # Full Profile Tactical Card
                st.markdown(f"""
                    <div class="strike-zone-card">
                        <b style="color:#8b949e; font-size:0.65rem; display:block; margin-bottom:5px;">{stock['name'][:25]}</b>
                        <b style="color:#8b949e; font-size:0.7rem;">{status}</b><br>
                        <span class="val-entry">Entry: {stock['entry']:.2f}</span><br>
                        <span class="val-target">Target: {stock['target']:.2f}</span><hr style="border:0.1px solid #30363d; margin:8px 0;">
                        <span class="val-range">52W High: {stock['h52']:.2f}</span><br>
                        <span class="val-range">52W Low: {stock['l52']:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                leader_context += f"{stock['ticker']} ({stock['name']}, ${stock['price']:.2f}); "
        st.session_state.current_context = leader_context

    st.divider()
    st.write("### 🔍 Strategic Asset Search")
    query = st.text_input("Deep-Dive Ticker (e.g. RELIANCE.NS, TSLA):").upper()
    if query:
        try:
            q_t = yf.Ticker(query); q_h = q_t.history(period="2d"); q_i = q_t.info
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                e, t = (2*piv)-hi, (2*piv)-lo
                st.metric(label=f"{query} ({q_i.get('longName', '')})", value=f"{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"""
                    <div class="strike-zone-card">
                        <span class="val-entry">Entry: ${e:.2f}</span> | <span class="val-target">Target: ${t:.2f}</span><br>
                        <span class="val-range">52W Range: ${q_i.get('fiftyTwoWeekLow', 0):.2f} - ${q_i.get('fiftyTwoWeekHigh', 0):.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_research:
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []; st.rerun()

    suggestions = ["Explain the leaders", "What is Strike Zone?", "Nifty 50 Trend?"]
    s_cols = st.columns(3); clicked = None
    for idx, s in enumerate(suggestions):
        if s_cols[idx].button(s, use_container_width=True): clicked = s

    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        prompt = st.chat_input("Ask about the tape...")
        final_query = prompt if prompt else clicked
        if final_query:
            st.session_state.messages.append({"role": "user", "content": final_query})
            with st.chat_message("user"): st.write(final_query)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing market structure..."):
                    context = "Role: Senior Institutional Advisor. Context: " + st.session_state.current_context
                    ans = handle_ai_query(final_query, context, api_key)
                    st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
