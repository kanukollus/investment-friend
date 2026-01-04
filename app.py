import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# 1. ELITE WHITELABEL & SECRETS CONFIG
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

# Fetch Gemini API Key from Secrets
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

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
    .val-stop { color: #f85149; font-weight: bold; }
    
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; font-size: 0.88rem; border-radius: 0 8px 8px 0; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# 2. THE VOLATILITY ENGINE (Absolute Global Sort)
@st.cache_data(ttl=600)
def rank_global_movers():
    # Wikipedia Scraping with Browser Headers to avoid 403 Forbidden
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    symbols = pd.read_html(response.text)[0]['Symbol'].tolist()
    
    # Stratified Sampling to bypass ABC order and find true volatility
    sample = symbols[::12] 
    results = []
    for symbol in sample:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) < 2: continue
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            piv = (h['High'].iloc[-2] + h['Low'].iloc[-2] + prev) / 3
            results.append({
                "ticker": symbol, "price": curr, "change": ((curr-prev)/prev)*100,
                "entry": (2*piv)-h['High'].iloc[-2], 
                "target": (2*piv)-h['Low'].iloc[-2],
                "abs_change": abs(((curr-prev)/prev)*100)
            })
        except: continue
    # Forced Volatility Ranking (Bypasses Alphabetical Order)
    return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')

# 3. INTERFACE TABS
tab_tactical, tab_research = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk"])

with tab_tactical:
    st.write("### Today's Momentum Leaders")
    leaders = rank_global_movers()
    cols = st.columns(5)
    for i, stock in enumerate(leaders):
        with cols[i]:
            # Restore Status Labels (Strike Zone vs Overextended)
            status = "⚠️ OVEREXTENDED" if stock['price'] > stock['target'] else "✅ IN STRIKE ZONE"
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""
                <div class="strike-zone-card">
                    <b style="color: #8b949e; font-size: 0.7rem;">{status}</b><br>
                    <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                    <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                    <span class="val-stop">Stop: ${stock['entry']*0.985:.2f}</span>
                </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    # RESTORED UNIVERSAL SEARCH
    st.write("### 🔍 Strategic Asset Search")
    query = st.text_input("Deep-Dive any ticker (Zero Constraints):").upper()
    if query:
        try:
            q_t = yf.Ticker(query)
            q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2]
                piv = (q_h['High'].iloc[-2] + q_h['Low'].iloc[-2] + prev) / 3
                e, t = (2*piv)-q_h['High'].iloc[-2], (2*piv)-q_h['Low'].iloc[-2]
                st.metric(label=query, value=f"${p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"<div class='strike-zone-card'>Entry: ${e:.2f} | Target: ${t:.2f}</div>", unsafe_allow_html=True)
        except: st.error("Feed error.")

with tab_research:
    st.write("### AI Research Desk")
    if not GEMINI_KEY:
        st.error("Missing GEMINI_API_KEY in Secrets Settings.")
    else:
        user_msg = st.chat_input("Ask Gemini about setups or market strategy...")
        if user_msg:
            with st.chat_message("user"): st.write(user_msg)
            with st.chat_message("assistant"):
                # FIXED: Updated model to 'gemini-2.0-flash' to resolve 404 NotFound error
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(f"You are a Senior Institutional Advisor. Explain: {user_msg}")
                st.markdown(f"<div class='advisor-brief'>{response.text}</div>", unsafe_allow_html=True)
