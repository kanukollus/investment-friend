import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import google.generativeai as genai
import time
from google.api_core import exceptions

# --- 1. ARCHITECTURAL CONFIG & THEME ---
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    header, footer, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; height: 0; }
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem !important; border-radius: 12px; }
    .strike-zone-card { background-color: #010409; border: 1px solid #444c56; padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .thesis-box { background-color: #161b22; border-left: 4px solid #58a6ff; padding: 15px; margin-top: 10px; border-radius: 0 8px 8px 0; font-size: 0.9rem; line-height: 1.6; }
    .disclaimer-box { background-color: #1c1c1c; border: 1px solid #333; padding: 15px; border-radius: 8px; font-size: 0.75rem; color: #888; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_context" not in st.session_state: st.session_state.current_context = ""

# --- 3. PROFESSIONAL AI HANDLER (Tier 1 Optimized) ---
def get_pro_model(api_key):
    genai.configure(api_key=api_key)
    # Professional Tier allows for 1.5-Pro or Flash with massive quotas
    return "models/gemini-1.5-flash"

def generate_justification(ticker, price, api_key):
    """Generates a professional 3-point justification like the Alphabet example."""
    model_name = get_pro_model(api_key)
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    Act as a Senior Equity Analyst. Provide a concise 'Investment Thesis' for {ticker} trading at ${price}.
    Structure it as:
    1. Market Dominance/Moat.
    2. Operational Efficiency.
    3. Future Growth Catalyst.
    Keep it strictly professional and data-driven.
    """
    try:
        response = model.generate_content(prompt)
        return response.text if response and hasattr(response, 'text') else "Analysis unavailable."
    except Exception as e:
        return f"🚨 Analysis Offline: {str(e)}"

# --- 4. DATA ENGINE (v31.0 Base) ---
@st.cache_data(ttl=600)
def rank_movers(universe):
    idx = 1 if "India" in universe else 0
    url = "https://en.wikipedia.org/wiki/NIFTY_50" if idx == 1 else "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        syms = pd.read_html(resp.text)[idx]['Symbol'].tolist()
        if idx == 1: syms = [s + ".NS" for s in syms]
        res = []
        for s in syms[::max(1, len(syms)//40)]:
            try:
                t = yf.Ticker(s); h = t.history(period="2d")
                if len(h) < 2: continue
                c, prev, hi, lo = h['Close'].iloc[-1], h['Close'].iloc[-2], h['High'].iloc[-2], h['Low'].iloc[-2]
                p = (hi + lo + prev) / 3
                res.append({"ticker": s, "price": c, "change": ((c-prev)/prev)*100, "entry": (2*p)-hi, "target": (2*p)-lo, "abs": abs(((c-prev)/prev)*100)})
            except: continue
        return pd.DataFrame(res).sort_values(by='abs', ascending=False).head(5).to_dict('records')
    except: return []

# --- 5. INTERFACE ---
st.title("🏛️ Sovereign Intelligence Terminal")

exch = st.radio("Universe:", ["US (S&P 500)", "India (Nifty 50)"], horizontal=True)
tab_t, tab_r, tab_a = st.tabs(["⚡ Tactical", "🤖 Research Desk", "📜 Protocol"])

with tab_t:
    leaders = rank_movers(exch)
    curr = "₹" if "India" in exch else "$"
    if leaders:
        leader_ctx = ""
        cols = st.columns(5)
        for i, s in enumerate(leaders):
            with cols[i]:
                st.metric(label=s['ticker'], value=f"{curr}{s['price']:.2f}", delta=f"{s['change']:.2f}%")
                st.markdown(f"<div class='strike-zone-card'><span class='val-entry'>Entry: {curr}{s['entry']:.2f}</span><br><span class='val-target'>Target: {curr}{s['target']:.2f}</span></div>", unsafe_allow_html=True)
                leader_ctx += f"{s['ticker']}:{s['price']}; "
        st.session_state.current_context = leader_ctx
    
    st.divider()
    search = st.text_input("Strategic Search (Ticker):", key=f"s_{exch}").strip().upper()
    if search:
        api_key = st.secrets.get("GEMINI_API_KEY")
        try:
            q_t = yf.Ticker(search); q_h = q_t.history(period="2d")
            if not q_h.empty:
                p, prev, hi, lo = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2], q_h['High'].iloc[-2], q_h['Low'].iloc[-2]
                piv = (hi + lo + prev) / 3
                st.metric(label=search, value=f"{curr}{p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
                st.markdown(f"<div class='strike-zone-card'>Entry: {curr}{(2*piv)-hi:.2f} | Target: {curr}{(2*piv)-lo:.2f}</div>", unsafe_allow_html=True)
                
                # PROFESSIONAL JUSTIFICATION BLOCK
                if api_key:
                    with st.spinner(f"Generating thesis for {search}..."):
                        thesis = generate_justification(search, p, api_key)
                        st.markdown(f"### 📈 Investment Thesis: {search}")
                        st.markdown(f"<div class='thesis-box'>{thesis}</div>", unsafe_allow_html=True)
            else: st.error("Ticker not found.")
        except: st.error("Data offline.")

with tab_r:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if st.button("🗑️ Reset Intelligence"): st.session_state.messages = []; st.rerun()
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    if prompt := st.chat_input("Ask Terminal..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            ans = model.generate_content(f"Market: {st.session_state.current_context}\nQuery: {prompt}").text
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

with tab_a:
    st.write("### 🏛️ Sovereign Protocol & Intelligence (v59.0)")
    st.markdown("""
    * **Tier 1 Scaling:** Billing-enabled account architecture unlocks **2,000 requests per minute**.
    * **Justification Engine:** Integrated fundamental investment theses for searched tickers.
    * **Strategic Search:** Universal ticker search with $S1/R1$ Pivot Math.
    * **State Persistence:** Session guards prevent crash errors during refreshes.
    """)

st.markdown("""<div class="disclaimer-box"><b>⚠️ DISCLAIMER:</b> Informational use only. You are solely responsible for your financial decisions.</div>""", unsafe_allow_html=True)
