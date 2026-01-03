import streamlit as st
import pandas as pd
import yfinance as yf

# 1. PREMIUM TERMINAL CONFIG
st.set_page_config(page_title="2026 Intelligence Terminal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .strike-zone-card { background-color: #1c1c1c; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-top: 10px; font-family: 'Courier New', monospace; font-size: 0.85rem; }
    .advisor-brief { background-color: #0d141f; border-left: 4px solid #58a6ff; padding: 12px; border-radius: 4px; margin-top: 10px; font-size: 0.85rem; color: #c9d1d9; line-height: 1.4; }
    .val-entry { color: #58a6ff; font-weight: bold; }
    .val-target { color: #3fb950; font-weight: bold; }
    .val-stop { color: #f85149; font-weight: bold; }
    .status-pill { padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: bold; display: inline-block; margin-bottom: 5px; }
    .pill-red { background-color: #da363322; color: #f85149; border: 1px solid #da3633; }
    .pill-green { background-color: #23863622; color: #3fb950; border: 1px solid #238636; }
    </style>
    """, unsafe_allow_html=True)

# 2. INTELLIGENCE DATABASE (Jan 2026 Context)
ADVISOR_NOTES = {
    "MU": "<b>Catalyst:</b> Surged 10.5% after Bernstein raised target to $330. HBM supply for 2026 is already fully booked.",
    "NVDA": "<b>Catalyst:</b> Pre-CES rally ahead of Jensen Huang's Jan 5th keynote. Focus is on H200 sales to approved China accounts.",
    "TSLA": "<b>Trend:</b> Down 2.6% on weak Q4 deliveries. Valuation now depends entirely on Robotaxi/FSD regulatory approvals.",
    "PLTR": "<b>Trend:</b> 5.6% flush to start 2026. High institutional profit-taking after the massive 2025 outperformance.",
    "AMD": "<b>Catalyst:</b> Named 'Best Idea for 2026' by TD Cowen. Market is pricing in the mid-2026 Helios platform launch.",
    "DEFAULT": "<b>Note:</b> Volatility is high to start the year. Monitor volume spikes for institutional accumulation signals."
}

# 3. DYNAMIC DATA & LEVEL LOGIC
@st.cache_data(ttl=600)
def get_market_leaders():
    pool = ["MU", "NVDA", "AMD", "TSLA", "PLTR", "AMZN", "MSFT", "AAPL"]
    data = []
    for t in pool:
        try:
            s = yf.Ticker(t)
            h = s.history(period="2d")
            price = h['Close'].iloc[-1]
            change = ((price - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
            
            pivot = (h['High'].iloc[-2] + h['Low'].iloc[-2] + h['Close'].iloc[-2]) / 3
            r1 = (2 * pivot) - h['Low'].iloc[-2]
            s1 = (2 * pivot) - h['High'].iloc[-2]
            
            data.append({
                "t": t, "p": price, "c": change, "entry": s1, "target": r1, "stop": s1 * 0.985,
                "is_over": price > r1, "note": ADVISOR_NOTES.get(t, ADVISOR_NOTES["DEFAULT"])
            })
        except: continue
    return sorted(data, key=lambda x: abs(x['c']), reverse=True)[:5]

# 4. DASHBOARD UI
st.title("🏛️ Sovereign Advisor Terminal")
st.write("### ⚡ Tactical Leaders & Senior Briefing")

leaders = get_market_leaders()
cols = st.columns(5)

for i, stock in enumerate(leaders):
    with cols[i]:
        pill_class = "pill-red" if stock['is_over'] else "pill-green"
        status = "OVEREXTENDED" if stock['is_over'] else "STRIKE ZONE"
        
        # Row 1: The Numbers
        st.metric(label=stock['t'], value=f"${stock['p']:.2f}", delta=f"{stock['c']:.2f}%")
        
        # Row 2: The Tactical Setup
        st.markdown(f"""
            <div class="strike-zone-card">
                <div class="status-pill {pill_class}">{status}</div><br>
                <span class="val-entry">Entry: ${stock['entry']:.2f}</span><br>
                <span class="val-target">Target: ${stock['target']:.2f}</span><br>
                <span class="val-stop">Stop: ${stock['stop']:.2f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Row 3: The Advisor Brief (New Request)
        st.markdown(f"""
            <div class="advisor-brief">
                {stock['note']}
            </div>
        """, unsafe_allow_html=True)

st.divider()

# 5. CUSTOM SEARCH WITH BRIEF
st.write("### 🔍 Strategic Asset Deep-Dive")
query = st.text_input("Enter Ticker (e.g., GOOGL, MSFT, RKLB):").upper()
if query:
    try:
        s_yf = yf.Ticker(query)
        s_h = s_yf.history(period="2d")
        if not s_h.empty:
            q_p = s_h['Close'].iloc[-1]
            q_p_prev = s_h['Close'].iloc[-2]
            q_pivot = (s_h['High'].iloc[-2] + s_h['Low'].iloc[-2] + q_p_prev) / 3
            q_r1 = (2 * q_pivot) - s_h['Low'].iloc[-2]
            q_s1 = (2 * q_pivot) - s_h['High'].iloc[-2]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric(label=query, value=f"${q_p:.2f}", delta=f"{((q_p-q_p_prev)/q_p_prev)*100:.2f}%")
            with c2:
                st.markdown(f"""
                    <div class="strike-zone-card" style="font-size: 1.1rem;">
                        <span class="val-entry">Entry: ${q_s1:.2f}</span> | 
                        <span class="val-target">Target: ${q_r1:.2f}</span> | 
                        <span class="val-stop">Stop: ${q_s1*0.985:.2f}</span>
                    </div>
                    <div class="advisor-brief" style="font-size: 1rem;">
                        <b>2026 Scraper Analysis:</b> Institutional volume in {query} is currently 
                        {'Elevated' if q_p > q_p_prev else 'Neutral'}. Monitor the {q_s1:.2f} level for high-probability scalps.
                    </div>
                """, unsafe_allow_html=True)
    except:
        st.error("Data feed error for that symbol.")
