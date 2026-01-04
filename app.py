import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import datetime

# --- 1. PAGE CONFIG & WHITELABEL CSS (Vedic-Inspired) ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* Absolute Whitelabel: Hides all UI noise */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    
    /* Metrics & Tactical Cards */
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; border-radius: 0 8px 8px 0; font-size: 0.88rem;}
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; border-bottom: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE (Vedic Logic) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. DYNAMIC GEMINI ENGINE (Vedic Logic) ---
def get_working_model(key):
    genai.configure(api_key=key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prefer flash for speed, fallback to whatever is first available
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash'
        return available[0]
    except: return "models/gemini-1.5-flash"

def handle_ai_query(prompt, context, key):
    try:
        model_name = get_working_model(key)
        model = genai.GenerativeModel(model_name)
        # We start a chat with the financial context as the first message
        full_prompt = f"System Context: {context}\n\nUser Question: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        if "429" in str(e): return "⚠️ Quota Exceeded. Please wait 60 seconds."
        return f"AI Error: {str(e)}"

# --- 4. DATA ENGINE (Market Logic) ---
@st.cache_data(ttl=600)
def rank_global_movers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    symbols = pd.read_html(response.text)[0]['Symbol'].tolist()
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
    df = pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5)
    return df.to_dict('records')

# --- 5. UI TABS ---
tab_tactical, tab_research = st.tabs(["⚡ Tactical Terminal", "🤖 AI Analyst Desk"])

with tab_tactical:
    st.write("### Today's Momentum Leaders")
    leaders = rank_global_movers()
    cols = st.columns(5)
    
    # Building a context string for the AI so it knows what the "Leaders" are
    leader_context = "Top Movers Today: "
    
    for i, stock in enumerate(leaders):
        with cols[i]:
            status = "⚠️ OVEREXTENDED" if stock['price'] > stock['target'] else "✅ IN STRIKE ZONE"
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""<div class="strike-zone-card">
                <b style="color: #8b949e; font-size: 0.7rem;">{status}</b><br>
                <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                <span class="val-target">Target: ${stock['target']:.2f}</span>
            </div>""", unsafe_allow_html=True)
            leader_context += f"{stock['ticker']} (${stock['price']:.2f}, {stock['change']:.2f}%); "

    st.divider()
    st.write("### 🔍 Strategic Asset Search")
    query = st.text_input("Enter Ticker (e.g. NVDA, RKLB):").upper()
    
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
                # Update AI context with searched ticker
                st.session_state.current_context = f"Analyzing {query}: Price ${p:.2f}, Entry ${e:.2f}, Target ${t:.2f}. " + leader_context
        except: st.error("Feed error.")
    else:
        st.session_state.current_context = leader_context

with tab_research:
    st.write("### AI Analyst Desk")
    api_key = st.secrets.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    else:
        # Show Chat History (Vedic Logic)
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        # Suggestions (Vedic Logic)
        suggestions = ["Explain the APP flush", "Define Strike Zone", "Analyze leaders"]
        cols = st.columns(3); clicked = None
        for i, s in enumerate(suggestions):
            if cols[i].button(s, use_container_width=True): clicked = s

        if (prompt := st.chat_input("Ask about the tape...")) or clicked:
            final_prompt = prompt if prompt else clicked
            st.session_state.messages.append({"role": "user", "content": final_prompt})
            with st.chat_message("user"): st.write(final_prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing market structure..."):
                    context = "You are a Senior Institutional Investment Advisor in 2026. " + st.session_state.current_context
                    ans = handle_ai_query(final_prompt, context, api_key)
                    st.markdown(f"<div class='advisor-brief'>{ans}</div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
