import streamlit as st

# 1. WHITELABEL & MOBILE MOBILE-FIRST CSS
st.set_page_config(page_title="Sovereign Terminal", layout="wide")

# Using st.html for 2026 performance and zero-latency injection
st.html("""
    <style>
    /* HIDE TOP NAV & STREAMLIT ELEMENTS */
    header, footer, [data-testid="stToolbar"], .stDeployButton { visibility: hidden !important; height: 0 !important; }
    #MainMenu { visibility: hidden !important; }
    
    /* BACKGROUND & FONT READABILITY */
    .stApp { background-color: #0d1117; } /* Deep Slate */
    
    /* CUSTOM METRIC CARD (Mobile Optimized) */
    [data-testid="stMetric"] {
        background-color: #161b22; 
        border: 1px solid #30363d; 
        padding: 1.2rem !important;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    /* FIXING YOUR APP COLOR REABILITY */
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.9rem !important; }
    [data-testid="stMetricValue"] { color: #f0f6fc !important; font-weight: 700 !important; }
    
    /* STRIKE ZONE CARD (High Contrast) */
    .strike-zone-card {
        background-color: #1c2128;
        border: 1px solid #444c56;
        padding: 15px;
        border-radius: 10px;
        font-family: 'JetBrains Mono', 'Roboto Mono', monospace;
    }
    .val-entry { color: #58a6ff; } /* Strategic Blue */
    .val-target { color: #3fb950; } /* Profit Green */
    .val-stop { color: #f85149; } /* Risk Red */
    
    /* ADVISOR BRIEF (Mobile Spacing) */
    .advisor-brief {
        background-color: #0d1117;
        border-left: 3px solid #d29922; /* Gold Accents */
        color: #e6edf3;
        padding: 12px;
        margin-top: 10px;
        font-size: 0.85rem;
    }
    </style>
""")

# 2. IMPLEMENTATION (Example based on your screenshot)
st.title("🏛️ Sovereign Intelligence Terminal")
st.markdown("### ⚡ Live Momentum Leaders")

# Example for AppLovin (APP) from your screenshot
col1, col2 = st.columns([1, 1]) # Stacks on mobile automatically

with col1:
    st.metric(label="APP", value="$618.32", delta="-8.24%")
    
    # Strike Zone using the new Mobile CSS
    st.markdown("""
        <div class="strike-zone-card">
            <b style="color: #8b949e; font-size: 0.7rem;">STRIKE ZONE</b><br>
            <span class="val-entry">Entry: $664.47</span><br>
            <span class="val-target">Target: $690.98</span><br>
            <span class="val-stop">Stop: $654.50</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="advisor-brief">
            <b>AppLovin</b> is seeing an aggressive technical flush. 
            Watch S1 for a reversal scalp.
        </div>
    """, unsafe_allow_html=True)
