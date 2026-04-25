import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import os
import json
import google.generativeai as genai

def get_gemini_api_key():
    # Prefer Streamlit secrets in deployment, then environment variable.
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY")
    except StreamlitSecretNotFoundError:
        secret_key = None
    if secret_key:
        return secret_key

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""

    with st.expander("🔑 How to get your Google Gemini API Key"):
        st.markdown("""
        1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Create or copy an API key
        3. Paste below
        """)
        st.session_state.gemini_api_key = st.text_input("Enter Gemini API Key", type="password")
    return st.session_state.gemini_api_key

def perform_ai_ats_analysis(text, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
        You are an expert ATS (Applicant Tracking System) resume reviewer. Analyze the resume below across these categories:

        1. Contact Information  
        2. Spelling & Grammar  
        3. Personal Pronoun Usage  
        4. Skills & Keyword Targeting  
        5. Complex or Long Sentences  
        6. Generic or Weak Phrases  
        7. Passive Voice Usage  
        8. Quantified Achievements  
        9. Required Resume Sections  
        10. AI-generated Language  
        11. Repeated Action Verbs  
        12. Visual Formatting or Readability  
        13. Personal Information / Bias Triggers  
        14. Other Strengths and Weaknesses  

        Return a **single valid JSON object**, and nothing else.

        The structure must follow this strict format:

        ```json
        {{
        "ATS_Score": (Analyse thoroughly and allot an ATS score to the resume, integer from 0 to 100),
        "Contact Information": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Spelling & Grammar": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        ...
        }}

        Rules:
            -   You MUST return valid JSON that can be parsed directly by Python's json.loads()
            -   Use double quotes for all keys and string values
            -   Do NOT include trailing commas
            -   Do NOT skip either the "Positives" or "Negatives" key — include both, even if the value is an empty list ([])
            -   Do NOT break the format or insert partial structures like "Positives": [], }}
            -   Do NOT output markdown, comments, explanations, or headings
            -   The ONLY output should be a clean JSON object (no preamble, no explanation)
            -   Every "Positives" and "Negatives" list should contain detailed, constructive, and example-backed feedback
            -   Be thorough and professionally critical, but fair

        Resume Text:
        {text}
        """

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        json_start = raw_text.find("{")
        json_end = raw_text.rfind("}") + 1

        if json_start == -1 or json_end == -1:
            st.error("❌ No JSON block detected in the AI response.")
            st.stop()

        json_str = raw_text[json_start:json_end]

        try:
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError as json_err:
            st.error(f"❌ Failed to parse AI response as JSON: {json_err}")
            st.code(json_str, language="json")
            st.stop()

    except Exception as e:
        st.error(f"❌ Unexpected error during AI analysis: {e}")
        st.stop()
