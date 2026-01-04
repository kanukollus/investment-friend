import streamlit as st
import google.generativeai as genai
import time

# --- 1. THE VEDIC MODEL DISCOVERY (FIXED) ---
@st.cache_data(ttl=3600)
def get_student_optimized_model(api_key):
    genai.configure(api_key=api_key)
    try:
        # Fetch the absolute latest list of what your specific key can access
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority 1: Gemini 3 Flash (Your new Student Pro access)
        if 'models/gemini-3-flash-preview' in available: return 'models/gemini-3-flash-preview'
        
        # Priority 2: Gemini 2.5 Flash (The current stable production model)
        if 'models/gemini-2.5-flash' in available: return 'models/gemini-2.5-flash'
        
        # Priority 3: Gemini 1.5 Flash (Legacy fallback)
        if 'models/gemini-1.5-flash' in available: return 'models/gemini-1.5-flash'
        
        return available[0] # Dynamic fallback to whatever works
    except:
        return "models/gemini-1.5-flash" # Absolute fallback

# --- 2. THE AI HANDLER (FIXED) ---
def handle_ai_query(prompt, context, key):
    # Discovery step ensures we never hardcode a broken model name
    model_name = get_student_optimized_model(key)
    try:
        model = genai.GenerativeModel(model_name)
        # Use the standard generate_content method
        response = model.generate_content(f"Context: {context[:400]}\nUser: {prompt}")
        if response and hasattr(response, 'text'):
            return response.text
        return "🚨 Model returned empty response (Check safety filters)."
    except Exception as e:
        return f"🚨 RAW ERROR: {str(e)}"
