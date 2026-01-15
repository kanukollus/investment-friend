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
    /* Absolute Whitelabel: Hides all Streamlit branding */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* Metrics & Tactical Signal Cards */
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.95rem !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }

    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-range { color: #8b949e; font-size: 0.75rem; font-family: monospace; }
    
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; border-bottom: 1px solid #30363d; }
    
    /* Disclaimer Styling */
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; line-height: 1.4; }
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
            return "⚠️ Quota Exceeded. Please wait 60s."

# --- 4. DATA ENGINE (Multi-Exchange & Full Profile) ---
# --- 4. DATA ENGINE (Filtered for Strike Zone) ---
# --- 4. DATA ENGINE (Low-Cost / High-Upside Optimization) ---
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
    
    sample = symbols[::max(1, len(symbols)//120)] # Scan roughly 120 symbols
    results = []
    
    for symbol in sample:
        try:
            t = yf.Ticker(symbol); h = t.history(period="2d")
            if len(h) < 2: continue
            info = t.info
            curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
            
            # Floor Trader Pivot Math
            piv = (hi + lo + prev) / 3
            target = (2*piv)-lo # Resistance 1
            entry = (2*piv)-hi   # Support 1
            
            # THE NEW FILTERS:
            if curr < 20: # 1. Only stocks under $20/₹20
                upside_pct = ((target - curr) / curr) * 100
                
                results.append({
                    "ticker": symbol, "name": info.get('longName', symbol), 
                    "price": curr, "change": ((curr-prev)/prev)*100,
                    "entry": entry, "target": target, "upside": upside_pct,
                    "h52": info.get('fiftyTwoWeekHigh', 0), "l52": info.get('fiftyTwoWeekLow', 0)
                })
        except: continue
        
    if not results: return []
    
    # Return top 5 stocks with the HIGHEST upside percentage
    return pd.DataFrame(results).sort_values(by='upside', ascending=False).head(5).to_dict('records')

# --- 5. UI INTERFACE (Inside tab_tactical) ---
# ... (Keep your tab definitions as they were) ...

    # UPDATED STRATEGIC SEARCH LOGIC (FIXES IN_ZONE ERROR)
    st.divider()
    st.write("### 🔍 Strategic Asset Search")
    query = st.text_input("Deep-Dive any ticker (e.g. RELIANCE.NS, TSLA):").upper()
    if query:
        try:
            q_t = yf.Ticker(query); q_h = q_t.history(period="2d"); q_i = q_t.info
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                e, t = (2*piv)-hi, (2*piv)-lo
                
                # Logic Fix: Define in_zone before using it
                in_zone = e <= p <= t
                status_text = "✅ IN STRIKE ZONE" if in_zone else "❌ OUTSIDE RANGE"
                status_color = "#3fb950" if in_zone else "#f85149"
                
                st.metric(label=f"{query} ({q_i.get('longName', '')})", value=f"{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"""
                    <div class="strike-zone-card">
                        <b style="color:{status_color}; font-size:0.8rem;">{status_text}</b><br>
                        <span class="val-entry">Entry: {e:.2f}</span> | <span class="val-target">Target: {t:.2f}</span><br>
                        <span class="val-range">52W Range: {q_i.get('fiftyTwoWeekLow', 0):.2f} - {q_i.get('fiftyTwoWeekHigh', 0):.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
        except: st.error("Ticker not found.")

with tab_research:
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []; st.rerun()

    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        # Suggestions
        suggestions = ["Explain the leaders", "What is Strike Zone?", "Nifty 50 Trend?"]
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
                with st.spinner("Reviewing tape..."):
                    context = "Role: Senior Institutional Advisor. Context: " + st.session_state.current_context
                    ans = handle_ai_query(final_query, context, api_key)
                    st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_about:
    st.markdown("""
    ### 🏛️ Institutional Protocol & Features
    The Sovereign Intelligence Terminal (v31.0) is an institutional-grade, zero-hardcode market analysis suite designed for the 2026 trading landscape.
    
    #### ⚡ Core Tactical Features
    * **Dynamic Market Discovery:** Real-time scrape of the S&P 500 (US) or Nifty 50 (India) without static ticker pools.
    * **Volatility-First Ranking:** Stratified scan identifying leaders by absolute magnitude of percentage change.
    * **Institutional Pivot Math:** Every asset is analyzed via floor-trader pivot points:
        - **Entry (S1):** Calculated institutional defense level.
        - **Target (R1):** Resistance ceiling for profit-taking.
        - **Stop Loss:** Hardcoded 1.5% safety net from Entry.
    * **Full Security Profiling:** Identity names and 52-Week High/Low data for all assets.
    * **Universal Strategic Search:** Zero-constraint search bar for Equities, Crypto, and Global Stocks.
    
    #### 🤖 AI Research Desk (Stability Optimized)
    * **Vedic-Style Contextual Intelligence:** AI receives live serialized snapshots of terminal data for institutional accuracy.
    * **Dynamic Model Discovery:** Audits available models to prioritize high-throughput engines like Gemini 1.5 Flash.
    * **Advanced Rate-Limit Guard:** Exponential Backoff and Pro-active Throttling to handle 429 "Resource Exhausted" errors.
    
    #### 📱 Whitelabel UI & Infrastructure
    * **Stealth Branding:** Custom CSS removes all Streamlit headers, toolbars, and "Deploy" icons.
    * **OLED Contrast Theme:** High-contrast palette optimized for mobile and outdoor readability.
    * **Global Exchange Switching:** Instant toggle between US ($) and India (₹) with automatic ticker normalization.
    """)

# --- GLOBAL DISCLAIMER FOOTER ---
st.markdown("""
    <div class="disclaimer-box">
        <b>⚠️ INSTITUTIONAL DISCLAIMER:</b> This terminal is for informational and educational purposes only. 
        It does not constitute financial, investment, or legal advice. All trading involves substantial risk of loss. 
        Calculations are based on historical data and do not guarantee future performance. 
        <b>USER RESPONSIBILITY:</b> By using this application, you acknowledge that you are solely responsible 
        for your own investment decisions and any resulting financial actions. The developers of this terminal 
        accept no liability for any losses or damages incurred.
    </div>
""", unsafe_allow_html=True)
