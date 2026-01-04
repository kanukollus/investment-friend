import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai

# --- 1. PAGE CONFIG & RESTORED TITLE ---
st.set_page_config(page_title="Sovereign Intelligence Terminal", layout="wide")

st.markdown("""
    <style>
    /* Full Whitelabel: Hides all Streamlit branding */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* Metrics & Tactical Signal Cards (OLED Optimized) */
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.95rem !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }

    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; border-bottom: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE & AI UTILITIES ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

def get_working_model(key):
    genai.configure(api_key=key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-2.0-flash' in available: return 'models/gemini-2.0-flash'
        return available[0]
    except: return "models/gemini-1.5-flash"

def handle_ai_query(prompt, context, key):
    try:
        model = genai.GenerativeModel(get_working_model(key))
        full_prompt = f"System Context: {context}\n\nUser Question: {prompt}"
        return model.generate_content(full_prompt).text
    except Exception as e:
        return f"⚠️ AI Service Busy: {str(e)}"

# --- 3. THE VOLATILITY ENGINE ---
@st.cache_data(ttl=600)
def rank_global_movers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    symbols = pd.read_html(response.text)[0]['Symbol'].tolist()
    
    sample = symbols[::12] # Global stratified sample
    results = []
    for symbol in sample:
        try:
            t = yf.Ticker(symbol); h = t.history(period="2d")
            if len(h) < 2: continue
            curr, prev, high, low = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
            
            # Pivot Math
            piv = (high + low + prev) / 3
            results.append({
                "ticker": symbol, "price": curr, "change": ((curr-prev)/prev)*100,
                "entry": (2*piv)-high, "target": (2*piv)-low,
                "abs_change": abs(((curr-prev)/prev)*100)
            })
        except: continue
    return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')

# --- 4. MAIN INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")

tab_tactical, tab_research = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk"])

with tab_tactical:
    st.write("### Today's Momentum Leaders")
    leaders = rank_global_movers()
    leader_context = "Market Leaders: "
    
    cols = st.columns(5)
    for i, stock in enumerate(leaders):
        with cols[i]:
            status = "⚠️ OVEREXTENDED" if stock['price'] > stock['target'] else "✅ IN STRIKE ZONE"
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""<div class="strike-zone-card">
                <b style="color: #8b949e; font-size: 0.7rem;">{status}</b><br>
                <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                <span class="val-target">Target: ${stock['target']:.2f}</span>
            </div>""", unsafe_allow_html=True)
            leader_context += f"{stock['ticker']} (${stock['price']:.2f}); "

    st.divider()
    st.write("### 🔍 Strategic Asset Search")
    query = st.text_input("Enter Ticker (e.g., TSLA, RKLB, BTC-USD):").upper()
    if query:
        try:
            q_t = yf.Ticker(query); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev, high, low = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (high + low + prev) / 3
                e, t = (2*piv)-high, (2*piv)-low
                st.metric(label=query, value=f"${p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"<div class='strike-zone-card'>Entry: ${e:.2f} | Target: ${t:.2f}</div>", unsafe_allow_html=True)
                st.session_state.current_context = f"Analyzing {query}: ${p:.2f}. " + leader_context
        except: st.error("Ticker not found.")
    else: st.session_state.current_context = leader_context

with tab_research:
    c1, c2 = st.columns([4, 1])
    with c1: st.write("### AI Research Desk")
    with c2: 
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.rerun()

    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("Missing API Key in Secrets.")
    else:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        if (prompt := st.chat_input("Ask about setups...")):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    context = "Tone: Senior Institutional Advisor. Context: " + st.session_state.current_context
                    ans = handle_ai_query(prompt, context, api_key)
                    st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
