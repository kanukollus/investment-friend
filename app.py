import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
import random

# --- 1. PAGE CONFIG & WHITESPACE THEME ---
st.set_page_config(page_title="Sovereign Intelligence Terminal", layout="wide")
st.markdown("""<style>
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden !important; }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .advisor-brief { background-color: #161b22; border-left: 4px solid #d29922; color: #e6edf3; padding: 12px; margin-top: 8px; font-size: 0.88rem; border-radius: 0 8px 8px 0; }
</style>""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. THE "VEDIC-STYLE" ROBUST AI HANDLER ---
def get_working_model(key):
    genai.configure(api_key=key)
    try:
        # 2026 logic: Prefer 1.5-flash if 2.0-flash is throttled (higher RPM)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash'
        return available[0]
    except: return "models/gemini-1.5-flash"

def handle_ai_query(prompt, context, key):
    # EXPONENTIAL BACKOFF: The "Vedic" secret for stability
    for attempt in range(3):
        try:
            model = genai.GenerativeModel(get_working_model(key))
            full_prompt = f"System Context: {context}\n\nUser Question: {prompt}"
            # 2026 Throttling: Forced wait to stay under 5 RPM
            time.sleep(random.uniform(1.5, 3.0)) 
            return model.generate_content(full_prompt).text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                # Wait longer on each fail (3s, 6s)
                time.sleep((attempt + 1) * 3)
                continue
            return f"⚠️ Service Busy: Quota exceeded (5 RPM Limit). Retry in 30s."

# --- 4. VOLATILITY ENGINE ---
@st.cache_data(ttl=600)
def rank_global_movers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        symbols = pd.read_html(response.text)[0]['Symbol'].tolist()
        sample = symbols[::12]
        results = []
        for symbol in sample:
            t = yf.Ticker(symbol); h = t.history(period="2d")
            if len(h) < 2: continue
            curr, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
            piv = (hi + lo + prev) / 3
            results.append({
                "ticker": symbol, "price": curr, "change": ((curr-prev)/prev)*100,
                "entry": (2*piv)-hi, "target": (2*piv)-lo, "abs_change": abs(((curr-prev)/prev)*100)
            })
        return pd.DataFrame(results).sort_values(by='abs_change', ascending=False).head(5).to_dict('records')
    except: return []

# --- 5. MAIN UI ---
st.title("🏛️ Sovereign Intelligence Terminal")
tab_tactical, tab_research = st.tabs(["⚡ Tactical Terminal", "🤖 AI Research Desk"])

with tab_tactical:
    leaders = rank_global_movers()
    leader_context = "Top Movers: "
    cols = st.columns(5)
    for i, stock in enumerate(leaders):
        with cols[i]:
            status = "⚠️ OVEREXTENDED" if stock['price'] > stock['target'] else "✅ STRIKE ZONE"
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""<div class="strike-zone-card"><b style="color:#8b949e; font-size:0.7rem;">{status}</b><br><span class="val-entry">Entry: ${stock['entry']:.2f}</span><br><span class="val-target">Target: ${stock['target']:.2f}</span></div>""", unsafe_allow_html=True)
            leader_context += f"{stock['ticker']} (${stock['price']:.2f}); "
    
    st.divider()
    query = st.text_input("Deep-Dive Ticker (e.g. NVDA):").upper()
    if query:
        try:
            q_t = yf.Ticker(query); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                e, t = (2*piv)-hi, (2*piv)-lo
                st.metric(label=query, value=f"${p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"<div class='strike-zone-card'>Entry: ${e:.2f} | Target: ${t:.2f}</div>", unsafe_allow_html=True)
                st.session_state.current_context = f"Analyzing {query}: ${p:.2f}. " + leader_context
        except: st.error("Feed error.")
    else: st.session_state.current_context = leader_context

with tab_research:
    c_head, c_clear = st.columns([4, 1])
    with c_head: st.write("### AI Research Desk")
    with c_clear: 
        if st.button("🗑️ Clear"):
            st.session_state.messages = []; st.rerun()

    # SUGGESTIONS (Restored)
    suggestions = ["Explain APP flush", "Define Strike Zone", "Analyze leaders"]
    s_cols = st.columns(3)
    clicked = None
    for idx, s in enumerate(suggestions):
        if s_cols[idx].button(s, use_container_width=True): clicked = s

    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        prompt = st.chat_input("Analyze the tape...")
        final_query = prompt if prompt else clicked

        if final_query:
            st.session_state.messages.append({"role": "user", "content": final_query})
            with st.chat_message("user"): st.write(final_query)
            with st.chat_message("assistant"):
                with st.spinner("Reviewing price action..."):
                    context = "Role: Senior Institutional Advisor. Context: " + st.session_state.current_context
                    answer = handle_ai_query(final_query, context, api_key)
                    st.markdown(f"<div class='advisor-brief'>{answer}</div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
