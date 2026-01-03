import requests

# This function tells Yahoo: "I am a normal Chrome browser, not a server script."
def get_safe_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

@st.cache_data(ttl=3600)
def fetch_market_data(ticker):
    try:
        # Create a session to bypass IP-based blocking
        session = get_safe_session()
        yf_ticker = yf.Ticker(ticker, session=session)
        
        # Pull 5 days of data
        hist = yf_ticker.history(period="5d")
        
        if hist.empty:
            # If Yahoo returns nothing, try one more time with a different period
            hist = yf_ticker.history(period="1mo")
            
        return hist if not hist.empty else None
    except Exception:
        return None
