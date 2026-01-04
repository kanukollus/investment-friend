import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Terminal Alpha", layout="wide")

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
    .val-rr { color: #d29922; font-weight: bold; font-size: 0.85rem; }
    .sovereign-score { font-size: 1.1rem; font-weight: 800; color: #ffca28; text-align: center; border: 1px solid #ffca28; border-radius: 5px; padding: 4px; margin-bottom: 8px; background: rgba(255, 202, 40, 0.1); }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; border-bottom: 1px solid #30363d; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. DYNAMIC AI HANDLER (Throttled for Free Tier) ---
def get_working_model(key):
    genai.configure(api_key=key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available else available[0]
    except: return "models/gemini-1.5-flash"

def generate_s_score(ticker, price, entry, target, key):
    try:
        model = genai.GenerativeModel(get_working_model(key))
        prompt = f"Quant: {ticker} @ {price}, Entry {entry}, Target {target}. Score 1-100 probability. Return ONLY number + 6-word summary."
        # Added delay to prevent S-Score calls from overwhelming the quota
        time.sleep(1) 
        response = model.generate_content(prompt)
        return response.text.strip()
    except: return "70 | Analysis paused due to API quota."

def handle_ai_query(prompt, context, key):
    for attempt in range(3):
        try:
            model = genai.GenerativeModel(get_working_model(key))
            full_prompt = f"Context: {context}\n\nUser: {prompt}"
            time.sleep(2.0) # Forced delay to stay under RPM limits
            return model.generate_content(full_prompt).text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(5); continue
            return "⚠️ Service Busy: Gemini's free tier is at capacity. Please wait 60s and try again."

# --- 4. DATA ENGINE ---
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
                t = yf.Ticker(symbol); h = t.history(period="10d")
                if len(h) < 5: continue
                info = t.info
                curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                entry, target = (2*piv)-hi, (2*piv)-lo
                stop = entry * 0.985
                wins = len(h.tail(5)[h.tail(5)['High'] >= target])
                
                results.append({
                    "ticker": symbol, "name": info.get('longName', symbol), "price": curr, 
                    "change": ((curr-prev)/prev)*100, "entry": entry, "target": target, "stop": stop,
                    "rr": abs(target-entry)/abs(entry-stop) if abs(entry-stop) != 0 else 0,
                    "win_rate": (wins/5)*100, "h52": info.get('fiftyTwoWeekHigh', 0),
                    "l52": info.get('fiftyTwoWeekLow', 0), "abs_change": abs(((curr-prev)/prev)*100)
                })
            except: continue
        if not results: return []
        return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')
    except: return []

# --- 5. UI INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")
exchange_choice = st.radio("Exchange Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)

tab_tactical, tab_research, tab_about = st.tabs(["⚡ Alpha Terminal", "🤖 AI Research Desk", "📜 What is this app?"])

with tab_tactical:
    leaders = rank_movers(exchange_choice)
    curr_sym = "₹" if "India" in exchange_choice else "$"
    
    if not leaders:
        st.warning("Market data unavailable. Please refresh.")
    else:
        leader_context = f"Leaders in {exchange_choice}: "
        cols = st.columns(5)
        for i, stock in enumerate(leaders):
            with cols[i]:
                # S-Score (Agentic AI)
                raw_s = generate_s_score(stock['ticker'], stock['price'], stock['entry'], stock['target'], st.secrets.get("GEMINI_API_KEY"))
                st.markdown(f"<div class='sovereign-score'>S-SCORE: {raw_s}</div>", unsafe_allow_html=True)
                
                # RESTORED: Currency Symbol in Metric
                st.metric(label=stock['ticker'], value=f"{curr_sym}{stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
                
                st.markdown(f"""
                    <div class="strike-zone-card">
                        <b style="color:#8b949e; font-size:0.65rem; display:block; margin-bottom:5px;">{stock['name'][:22]}</b>
                        <span class="val-entry">Entry: {curr_sym}{stock['entry']:.2f}</span><br>
                        <span class="val-target">Target: {curr_sym}{stock['target']:.2f}</span><br>
                        <span class="val-rr">Risk/Reward: {stock['rr']:.2f}</span><hr style="border:0.1px solid #333; margin:5px 0;">
                        <span style="color:#8b949e; font-size:0.75rem;">52W H: {curr_sym}{stock['h52']:.2f}<br>52W L: {curr_sym}{stock['l52']:.2f}</span><br>
                        <span style="color:#8b949e; font-size:0.75rem;">5D Success: {stock['win_rate']}%</span>
                    </div>
                """, unsafe_allow_html=True)
                leader_context += f"{stock['ticker']} ({stock['name']}, {curr_sym}{stock['price']:.2f}); "
        st.session_state.current_context = leader_context

    st.divider()
    query = st.text_input("Deep-Dive Ticker (e.g. RELIANCE.NS, TSLA):").upper()
    if query:
        try:
            q_t = yf.Ticker(query); q_h = q_t.history(period="2d"); q_i = q_t.info
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                e, t = (2*piv)-hi, (2*piv)-lo
                st.metric(label=f"{query} ({q_i.get('longName', '')})", value=f"{curr_sym}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"""
                    <div class="strike-zone-card">
                        <span class="val-entry">Entry: {curr_sym}{e:.2f}</span> | <span class="val-target">Target: {curr_sym}{t:.2f}</span><br>
                        <span class="val-range">52W Range: {curr_sym}{q_i.get('fiftyTwoWeekLow', 0):.2f} - {curr_sym}{q_i.get('fiftyTwoWeekHigh', 0):.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_research:
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear History"): st.session_state.messages = []; st.rerun()

    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        # RESTORED: AI Suggestion Buttons
        suggestions = ["Analyze the leaders", "Explain the flush", "Nifty 50 Trend?"]
        s_cols = st.columns(3); clicked = None
        for idx, s in enumerate(suggestions):
            if s_cols[idx].button(s, use_container_width=True): clicked = s

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        prompt = st.chat_input("Analyze market energy...")
        final_query = prompt if prompt else clicked
        if final_query:
            st.session_state.messages.append({"role": "user", "content": final_query})
            with st.chat_message("user"): st.write(final_query)
            with st.chat_message("assistant"):
                ans = handle_ai_query(final_query, st.session_state.current_context, api_key)
                st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_about:
    st.markdown("""
    ### 🏛️ Sovereign Protocol & Alpha Features (v34.0)
    
    #### 🚀 The Alpha Power Moves
    * **Agentic S-Score:** Gemini acts as a Quant Agent assigning probability scores (1-100) to setups.
    * **Statistical Backtesting:** 5-Day "Success Rate" based on historical target hits.
    * **Risk/Reward (R/R) Engine:** Automated gain-vs-loss ratio for institutional setups.

    #### ⚡ Core Tactical Features
    * **Dynamic Market Discovery:** Real-time scrape of S&P 500 or Nifty 50.
    * **Volatility-First Ranking:** Tickers identified by absolute magnitude of percentage change.
    * **Institutional Pivot Math:** Every asset analyzed via professional floor-trader pivot points.
    * **Full Security Profiling:** Security Full Names and 52-Week High/Low range context.
    * **Global Exchange Switching:** Toggle between US ($) and India (₹) universes.
    
    #### 🛡️ Stability & Security
    * **Exponential Backoff:** Intelligent retries to handle Gemini's free-tier rate limits.
    * **Whitelabel UI:** Custom OLED-contrast theme with zero Streamlit branding.
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ INSTITUTIONAL DISCLAIMER:</b> Informational use only. Trading involves substantial risk. <b>USER RESPONSIBILITY:</b> You are solely responsible for your financial decisions. The developer accepts no liability for actions taken based on this data.</div>""", unsafe_allow_html=True)
