import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# 1. ELITE WHITELABEL & GEMINI CONFIG
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

# Replace with your actual Gemini API Key from Google AI Studio
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    genai.configure(api_key=GEMINI_API_KEY)

st.markdown("""
    <style>
    /* Full Whitelabel: Hides all Streamlit branding */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* Metrics & Signal Cards */
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; font-size: 0.88rem; border-radius: 0 8px 8px 0; }
    
    /* Center-Screen Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; justify-content: center; border-bottom: 1px solid #30363d; }
    .stTabs [data-baseweb="tab"] { font-size: 1rem; color: #8b949e; }
    .stTabs [aria-selected="true"] { color: #ffffff !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. SHARED DATA ENGINE
@st.cache_data(ttl=3600)
def get_sp500_raw():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    return pd.read_html(response.text)[0][['Symbol', 'Security']].values.tolist()

@st.cache_data(ttl=600)
def rank_global_movers(symbols):
    results = []
    step = len(symbols) // 60
    sample_universe = symbols[::step] 
    for symbol, name in sample_universe:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) < 2: continue
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            piv = (h['High'].iloc[-2] + h['Low'].iloc[-2] + prev) / 3
            results.append({
                "ticker": symbol, "name": name, "price": curr, "change": ((curr - prev) / prev) * 100,
                "entry": (2 * piv) - h['High'].iloc[-2], "target": (2 * piv) - h['Low'].iloc[-2],
                "abs_change": abs(((curr - prev) / prev) * 100)
            })
        except: continue
    df = pd.DataFrame(results)
    return df.sort_values(by='abs_change', ascending=False).head(5).to_dict('records')

# 3. MAIN INTERFACE TABS
tab_tactical, tab_research = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk"])

# --- TAB 1: TACTICAL TERMINAL ---
with tab_tactical:
    st.write("### Today's Momentum Leaders")
    
    
    if 'unlocked' not in st.session_state: st.session_state.unlocked = []
    
    universe = get_sp500_raw()
    leaders = rank_global_movers(universe)

    cols = st.columns(5)
    for i, stock in enumerate(leaders):
        with cols[i]:
            if i == 0 or stock['ticker'] in st.session_state.unlocked:
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
            else:
                st.metric(label=stock['ticker'], value="--", delta="Locked")
                if st.button(f"Analyze {stock['ticker']}", key=f"btn_{stock['ticker']}"):
                    st.session_state.unlocked.append(stock['ticker'])
                    st.rerun()

# --- TAB 2: AI RESEARCH DESK ---
with tab_research:
    st.write("### AI Intelligence Desktop")
    st.caption("Direct link to Gemini Institutional Advisor (2026 Model)")
    
    user_query = st.chat_input("Ask about setups, tickers, or strategy...")
    
    if user_query:
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            st.error("Gemini API Key missing. Access the code to input your key.")
        else:
            with st.chat_message("user"): st.write(user_query)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing the tape..."):
                    try:
                        model = genai.GenerativeModel('gemini-pro')
                        prompt = f"You are a Senior Institutional Investment Advisor in 2026. Answer concisely: {user_query}"
                        response = model.generate_content(prompt)
                        st.markdown(f"<div class='advisor-brief'>{response.text}</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"AI Service Interrupted: {e}")
