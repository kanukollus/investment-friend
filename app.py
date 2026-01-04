import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# 1. ELITE WHITELABEL & SECRETS CONFIG
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

# Securely fetch API Key from Streamlit Secrets
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

st.markdown("""
    <style>
    /* Absolute Whitelabeling */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* Metrics & Tactical Box Styling */
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem;}
    
    /* Responsive Tabs */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# 2. DATA ENGINE (Global Absolute Sorting)
@st.cache_data(ttl=600)
def rank_global_movers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    symbols = pd.read_html(response.text)[0]['Symbol'].tolist()
    # Sample step to ensure global diversity and bypass ABC order
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
                "entry": (2*piv)-h['High'].iloc[-2], "target": (2*piv)-h['Low'].iloc[-2],
                "abs_change": abs(((curr-prev)/prev)*100)
            })
        except: continue
    return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')

# 3. INTERFACE TABS
tab_tactical, tab_research = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk"])

with tab_tactical:
    st.write("### Today's Momentum Leaders")
    leaders = rank_global_movers()
    cols = st.columns(5)
    for i, stock in enumerate(leaders):
        with cols[i]:
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""<div class="strike-zone-card">
                <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                <span class="val-stop">Stop: ${stock['entry']*0.985:.2f}</span>
                </div>""", unsafe_allow_html=True)
    
    st.divider()
    # RESTORED SEARCH OPTION
    st.write("### 🔍 Strategic Asset Search")
    query = st.text_input("Analyze any ticker (e.g. NVDA, RKLB, AAPL):").upper()
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
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(f"Institutional Advisor tone: {user_msg}")
                st.markdown(f"<div class='advisor-brief'>{response.text}</div>", unsafe_allow_html=True)
