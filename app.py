import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# 1. ELITE WHITELABEL & OLED THEME
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

st.markdown("""
    <style>
    /* Full Whitelabel: Hides all Streamlit branding and UI noise */
    header, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { 
        visibility: hidden !important; height: 0 !important; display: none !important; 
    }
    
    /* OLED Mobile Optimization */
    .stApp { background-color: #0d1117; color: #f0f6fc; }
    [data-testid="stMetric"] { 
        background-color: #161b22; border: 1px solid #30363d; 
        padding: 1.2rem !important; border-radius: 12px; 
    }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }

    /* Tactical Signal Cards */
    .strike-zone-card { 
        background-color: #010409; border: 1px solid #444c56; 
        padding: 14px; border-radius: 10px; margin-top: 10px; font-family: monospace; 
    }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. THE VOLATILITY ENGINE (Absolute Sort Logic)
@st.cache_data(ttl=3600)
def get_sp500_raw():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    return pd.read_html(response.text)[0][['Symbol', 'Security']].values.tolist()

@st.cache_data(ttl=600)
def rank_by_real_momentum(universe):
    """Bypasses ABC order by ranking the entire top-tier by absolute change."""
    results = []
    # Scan a broad sample to ensure we find real movers
    for symbol, name in universe[:60]:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) < 2: continue
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            
            # Professional Pivot Calculations
            piv = (h['High'].iloc[-2] + h['Low'].iloc[-2] + prev) / 3
            results.append({
                "ticker": symbol, "price": curr, "change": pct,
                "entry": (2 * piv) - h['High'].iloc[-2],
                "target": (2 * piv) - h['Low'].iloc[-2]
            })
        except: continue
    
    # THE FIX: Create a DataFrame and sort by the ABSOLUTE value of the change
    # This ensures a stock at -8% or +8% beats a stock at +0.1% (like Apple or Amazon)
    df = pd.DataFrame(results)
    df['abs_change'] = df['change'].abs()
    return df.sort_values(by='abs_change', ascending=False).head(5).to_dict('records')

# 3. DASHBOARD
st.title("🏛️ Sovereign Terminal")
st.write("### ⚡ Live Momentum Leaders (Volatility Ranked)")

if 'unlocked' not in st.session_state:
    st.session_state.unlocked = []

with st.spinner("Executing Global Market Scan..."):
    universe = get_sp500_raw()
    leaders = rank_by_real_momentum(universe)

cols = st.columns(5)
for i, stock in enumerate(leaders):
    with cols[i]:
        # Rule: Show 1st mover, lock others until user action
        if i == 0 or stock['ticker'] in st.session_state.unlocked:
            st.metric(label=stock['ticker'], value=f"${stock['price']:.2f}", delta=f"{stock['change']:.2f}%")
            st.markdown(f"""
                <div class="strike-zone-card">
                    <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                    <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                    <span class="val-stop">Stop: ${stock['entry']*0.985:.2f}</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.metric(label=stock['ticker'], value="--", delta="Locked")
            if st.button(f"Load {stock['ticker']}", key=f"btn_{stock['ticker']}"):
                st.session_state.unlocked.append(stock['ticker'])
                st.rerun()

st.divider()
st.write("### 🔍 Tactical Search")
query = st.text_input("Deep-Dive any ticker (Zero Constraints):").upper()
if query:
    try:
        q_t = yf.Ticker(query)
        q_h = q_t.history(period="2d")
        if not q_h.empty:
            p, prev = q_h['Close'].iloc[-1], q_h['Close'].iloc[-2]
            piv = (q_h['High'].iloc[-2] + q_h['Low'].iloc[-2] + prev) / 3
            st.metric(label=query, value=f"${p:.2f}", delta=f"{((p-prev)/prev)*100:.2f}%")
            st.markdown(f"<div class='strike-zone-card'>Entry: ${(2*piv)-q_h['High'].iloc[-2]:.2f} | Target: ${(2*piv)-q_h['Low'].iloc[-2]:.2f}</div>", unsafe_allow_html=True)
    except: st.error("Feed error.")
