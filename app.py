import streamlit as st
import pandas as pd
import yfinance as yf

# 1. PREMIUM TERMINAL UI
st.set_page_config(page_title="2026 Strike Zone Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }
    [data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .signal-box { padding: 20px; border-radius: 10px; margin-top: 10px; font-family: 'Courier New', monospace; }
    .status-overextended { background-color: #2c1111; border: 1px solid #da3633; color: #f85149; }
    .status-strikezone { background-color: #062512; border: 1px solid #238636; color: #3fb950; }
    .label-blue { color: #58a6ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. THE TACTICAL ENGINE (Logic for Pivot Points)
def get_detailed_setup(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if len(hist) < 2: return None
        
        prev = hist.iloc[-2]  # Yesterday's data
        curr = hist.iloc[-1]  # Today's live data
        
        # Pivot Point Math
        pivot = (prev['High'] + prev['Low'] + prev['Close']) / 3
        r1 = (2 * pivot) - prev['Low']
        s1 = (2 * pivot) - prev['High']
        
        # Validation Logic
        current_price = curr['Close']
        is_overextended = current_price > r1
        
        return {
            "symbol": ticker.upper(),
            "price": current_price,
            "change": ((current_price - prev['Close']) / prev['Close']) * 100,
            "entry": s1,
            "target": r1,
            "stop": s1 * 0.985,
            "status": "⚠️ OVEREXTENDED" if is_overextended else "✅ IN STRIKE ZONE",
            "style": "status-overextended" if is_overextended else "status-strikezone",
            "roe": stock.info.get('returnOnEquity', 0) * 100
        }
    except: return None

# 3. HEADER & TOP 5 LEADERS
st.title("🎯 Sovereign Strike Zone Pro")
st.write("### ⚡ Today's Momentum Leaders")

symbols = ["NVDA", "TSLA", "PLTR", "MU", "AMD"]
cols = st.columns(5)

for i, t in enumerate(symbols):
    with cols[i]:
        setup = get_detailed_setup(t)
        if setup:
            st.metric(label=t, value=f"${setup['price']:.2f}", delta=f"{setup['change']:.2f}%")
            st.markdown(f"<div style='font-size: 0.8em; text-align: center;' class='{setup['style']}'>{setup['status']}</div>", unsafe_allow_html=True)

st.divider()

# 4. ENHANCEMENT: MANUAL SEARCH ENGINE
st.write("### 🔍 Custom Tactical Search")
search_ticker = st.text_input("Enter Ticker (e.g., AAPL, GOOGL, RKLB):", "").upper()

if search_ticker:
    with st.spinner(f"Analyzing {search_ticker} Pivot Points..."):
        custom_data = get_detailed_setup(search_ticker)
        
    if custom_data:
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.metric(label=custom_data['symbol'], value=f"${custom_data['price']:.2f}", delta=f"{custom_data['change']:.2f}%")
            st.write(f"**Fundamental Moat (ROE):** {custom_data['roe']:.1f}%")
            
        with c2:
            st.markdown(f"""
                <div class="signal-box {custom_data['style']}">
                    <h3 style="margin-top:0;">{custom_data['status']}</h3>
                    <hr style="border-color: #30363d;">
                    <span class="label-blue">Entry Level (S1):</span> ${custom_data['entry']:.2f}<br>
                    <span class="label-blue">Profit Target (R1):</span> ${custom_data['target']:.2f}<br>
                    <span class="label-blue">Stop Loss (1.5%):</span> ${custom_data['stop']:.2f}
                </div>
            """, unsafe_allow_html=True)
            
            if custom_data['status'] == "⚠️ OVEREXTENDED":
                st.warning(f"**Advisor Warning:** {custom_data['symbol']} is trading above its immediate resistance. Buying here is high risk. Wait for a pullback to ${custom_data['entry']:.2f}.")
    else:
        st.error("Invalid Ticker or Data Feed Offline. Please check the symbol.")

st.divider()

# 5. TECHNICAL EDUCATION SECTION
st.write("### 🏛️ Understanding the Pivot Strike Zone")

st.info("""
**Pivot Points** are the price levels professional 2026 algorithms use to set their trades. 
* **Entry (S1):** If the price drops here, it usually 'bounces' as algorithms buy the support.
* **Target (R1):** This is the 'ceiling.' Once reached, traders sell, causing the price to drop.
* **Overextended:** If a stock is above R1, the 'smart money' has already exited.
""")
