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
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.95rem !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-range { color: #8b949e; font-size: 0.75rem; font-family: monospace; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; border-bottom: 1px solid #30363d; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; line-height: 1.4; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. DYNAMIC AI HANDLER ---
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
            time.sleep(random.uniform(1.0, 2.0)) 
            return model.generate_content(full_prompt).text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep((attempt + 1) * 3)
                continue
            return "⚠️ Quota Exceeded. Please wait 60s."

# --- 4. DATA ENGINE (Under $20 Filter) ---
@st.cache_data(ttl=600)
def rank_movers(exchange_choice):
    if exchange_choice == "India (Nifty 50)":
        url = "https://en.wikipedia.org/wiki/NIFTY_50"
        symbols = [s + ".NS" for s in pd.read_html(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text)[1]['Symbol'].tolist()]
    else:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        symbols = pd.read_html(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text)[0]['Symbol'].tolist()
    
    sample = symbols[::max(1, len(symbols)//100)] 
    results = []
    
    for symbol in sample:
        try:
            t = yf.Ticker(symbol); h = t.history(period="2d")
            if len(h) < 2: continue
            curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
            
            if curr < 40: # YOUR FILTER
                piv = (hi + lo + prev) / 3
                target = (2*piv)-lo
                entry = (2*piv)-hi
                upside = ((target - curr) / curr) * 100
                
                results.append({
                    "ticker": symbol, "name": t.info.get('longName', symbol), 
                    "price": curr, "upside": upside, "entry": entry, "target": target,
                    "h52": t.info.get('fiftyTwoWeekHigh', 0), "l52": t.info.get('fiftyTwoWeekLow', 0)
                })
        except: continue
    
    if not results: return []
    return pd.DataFrame(results).sort_values(by='upside', ascending=False).head(5).to_dict('records')

# --- 5. UI INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Exchange Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

# THE CRITICAL FIX: TAB DEFINITION
tab_tactical, tab_research, tab_about = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk", "📜 What is this app?"])

with tab_tactical:
    st.write(f"### {exchange_choice} High-Upside Stocks (<$40)")
    leaders = rank_movers(exchange_choice)
    
    context_text = ""
    if not leaders:
        st.warning("No assets under $20 found in this sample. Try another exchange.")
    else:
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                st.metric(label=stock['ticker'], value=f"{stock['price']:.2f}", delta=f"{stock['upside']:.1f}% Upside")
                st.markdown(f"""
                    <div class="strike-zone-card">
                        <span class="val-entry">Entry: {stock['entry']:.2f}</span><br>
                        <span class="val-target">Target: {stock['target']:.2f}</span><br>
                        <span class="val-range">52W L: {stock['l52']:.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
                context_text += f"{stock['ticker']} (Upside {stock['upside']:.1f}%); "
        st.session_state.current_context = context_text

    st.divider()
    st.write("### 🔍 Strategic Asset Search")
    query = st.text_input("Deep-Dive any ticker:").upper()
    if query:
        try:
            q_t = yf.Ticker(query); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                e, t = (2*piv)-hi, (2*piv)-lo
                in_zone = e <= p <= t
                status_color = "#3fb950" if in_zone else "#f85149"
                st.metric(label=query, value=f"{p:.2f}")
                st.markdown(f"<div class='strike-zone-card' style='border-color:{status_color}'>Entry: {e:.2f} | Target: {t:.2f}</div>", unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_research:
    st.write("### AI Research Desk")
    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        prompt = st.chat_input("Analyze markets...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            with st.chat_message("assistant"):
                ans = handle_ai_query(prompt, st.session_state.current_context, api_key)
                st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": ans})
    else:
        st.error("Missing API Key in Secrets.")

with tab_about:
    st.write("### Institutional Protocol")
    st.info("Scanner prioritizing equities under $40 with the highest Pivot Resistance upside.")

st.markdown('<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Not financial advice.</div>', unsafe_allow_html=True)
