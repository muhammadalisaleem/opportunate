import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import google.generativeai as genai
import os
import re

# Function to get API key from Streamlit secrets or user input
def get_gemini_api_key():
    # Attempt to get from Streamlit secrets first (for deployment)
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY")
    except StreamlitSecretNotFoundError:
        secret_key = None
    if secret_key:
        return secret_key

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    # If not in secrets, prompt user for it
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""

    with st.expander("🔑 **How to get your Google Gemini API Key**"):
        st.markdown(
            """
            1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey).
            2. Log in with your Google account.
            3. Click on "Create API key in new project" or copy an existing one.
            4. Paste your API key in the input box below.
            """
        )
        st.session_state.gemini_api_key = st.text_input(
            "Enter your Google Gemini API Key:",
            type="password",
            value=st.session_state.gemini_api_key,
            key="gemini_api_input"
        )
        st.markdown(
            """
            <small><i>Note: The Gemini API has free tier usage limits (e.g., requests per minute, tokens per day). If you encounter errors like 'Quota Exceeded,' please wait a few minutes or check your usage on Google AI Studio.</i></small>
            """, unsafe_allow_html=True
        )
    return st.session_state.gemini_api_key

@st.cache_data(ttl=3600) # Cache the model list for an hour
def list_available_gemini_models(api_key):
    """Lists available Gemini models that support generateContent."""
    if not api_key:
        return []
    try:
        genai.configure(api_key=api_key)
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        return models
    except Exception as e:
        if "API key not valid" not in str(e) and "Authentication error" not in str(e) and api_key:
            st.error(f"Error listing Gemini models: {e}. This might indicate a problem with your API key or network.")
        return []

def get_suitable_gemini_model(api_key):
    """
    Finds a suitable Gemini model for text generation, preferring newer and non-vision specific models.
    """
    available_models = list_available_gemini_models(api_key)
    
    if not available_models:
        return None

    # Ordered list of preferred text-generation models
    preferred_models_order = [
        "gemini-2.5-flash",              #  Best balance of quality, speed, and cost
        "gemini-1.5-flash-8b",           #  Budget-friendly small model with good capabilities
        "gemini-2.0-flash",              #  Stable, older but still versatile
        "gemini-2.0-flash-lite",         #  Lightweight fallback for quota-limited use
        "gemini-1.5-flash-latest"
    ]

    
    selected_model = None
    for preferred_model_name in preferred_models_order:
        for model in available_models:
            if model.name == preferred_model_name or model.name == f"models/{preferred_model_name}":
                selected_model = model.name
                break
        if selected_model:
            break

    if selected_model:
        # Check if the selected model is specifically a vision model when not explicitly needed
        # and try to find a pure text one as a fallback for older vision models.
        # Newer 1.5 models are multimodal and handle text well, so don't filter them out.
        is_vision_only_model = "vision" in selected_model.lower() and not ("gemini-1.5-flash" in selected_model or "gemini-1.5-pro" in selected_model)
        
        if is_vision_only_model:
            # Try to find a non-vision model among available ones
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods and "vision" not in model.name.lower():
                    return model.name
            return selected_model
        else:
            return selected_model
            
    # If no preferred model found, return the first available general text model
    for model in available_models:
        if 'generateContent' in model.supported_generation_methods and "vision" not in model.name.lower():
            return model.name
            
    # If all else fails, return the first model found that supports generateContent (could be vision)
    for model in available_models:
        if 'generateContent' in model.supported_generation_methods:
            return model.name

    return None

def generate_prompt(section_name, text_content, tone="Professional"):
    """
    Generates a tailored prompt for Gemini based on the section and desired tone.
    """
    base_prompt = f"As an expert resume writer, rewrite the following {section_name} to be highly impactful, concise, and ATS-friendly, using a {tone} tone. Focus on achievements, quantifiable results, and strong action verbs. Avoid generic statements and focus on unique contributions."

    if section_name == "professional summary":
        return f"{base_prompt} Ensure it is between 30 to 70 words.\n\nHere is the summary:\n{text_content}\n\nEnhanced Professional Summary (30-70 words):"
    elif section_name == "job responsibility":
        # Request max 3 bullet points, without headers or extra formatting with estimated numeric statistics.
        return f"Rewrite the following job responsibilities into a maximum of 3 concise, impactful bullet points. Each bullet point should start with a strong action verb and focus on quantifiable achievements. If specific numbers are not provided, estimate reasonable numeric statistics (e.g., 'increased efficiency by 20%', 'reduced errors by 15%') to demonstrate impact. Do NOT include any headers, introductory text, or concluding remarks. Provide ONLY the bullet points, one per line.\n\nHere are the job responsibilities:\n{text_content}\n\nEnhanced Responsibilities (max 3 bullet points with quantifiable results). Just give plain text with no sort of formatting:"
    elif section_name == "project description":
        # Request max 3 bullet points, without headers or extra formatting with estimated numeric statistics.
        return f"Rewrite the following project descriptions into a maximum of 3 concise, impactful bullet points. Each bullet point should start with a strong action verb and highlight contributions and results. If specific numbers are not provided, estimate reasonable numeric statistics (e.g., 'improved performance by 25%', 'handled 500+ users') to demonstrate impact. Do NOT include any headers, introductory text, or concluding remarks. Provide ONLY the bullet points, one per line.\n\nHere are the project descriptions:\n{text_content}\n\nEnhanced Project Descriptions (max 3 bullet points with quantifiable results). Just give plain text with no sort of formatting:"
    elif section_name == "skills section":
        # Request specific format for skills: Technical Skills: ..., Soft Skills: ...
        return f"From the following text, extract and categorize all relevant technical skills and soft skills. List 'Technical Skills' as a comma-separated string on one line, and 'Soft Skills' as a comma-separated string on the next line. Do NOT include any other text, headers, or formatting. Ensure no duplicate skills. Moreover, from the extracted skills, add more closely connected skills toh the list you return. If a category has no skills, just leave it blank after the colon.\n\nExample Output:\nTechnical Skills: Python, Java, AWS, SQL\nSoft Skills: Leadership, Communication, Problem-solving\n\nText to extract skills from:\n{text_content}\n\nEnhanced Skills Section:"
    elif section_name == "achievements":
        return f"Rewrite the following achievements into concise, keyword-rich, and impactful sentences. Focus on quantifiable results where possible. If an achievement is vague, make a reasonable professional interpretation. Separate each achievement sentence with a comma. Do NOT include any introductory or concluding sentences, just the comma-separated sentences.\n\nAchievements:\n{text_content}\n\nEnhanced Achievements:"
    else:
        return f"{base_prompt}\n\nHere is the content:\n{text_content}\n\nEnhanced Content:"


def enhance_content_with_gemini(section_name, text_content, tone, api_key):
    """
    Sends content to Google Gemini for enhancement.
    """
    if not api_key:
        st.error("Gemini API key is not provided. Please enter your API key to use AI enhancement.")
        return text_content # Return original content if no API key

    model_name = get_suitable_gemini_model(api_key)
    if not model_name:
        st.error(f"No suitable Gemini model found for generation with your API key. Please check available models on Google AI Studio.")
        return text_content

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        prompt = generate_prompt(section_name, text_content, tone)
        
        response = model.generate_content(
            prompt,
            safety_settings={
                'HARASSMENT': 'BLOCK_NONE',
                'HATE': 'BLOCK_NONE',
                'SEXUAL': 'BLOCK_NONE',
                'DANGEROUS': 'BLOCK_NONE'
            }
        )
        
        if response and response.parts:
            enhanced_text = ""
            for part in response.parts:
                if hasattr(part, 'text'):
                    enhanced_text += part.text
            return enhanced_text.strip()
        else:
            st.warning(f"AI enhancement returned an empty or unexpected response for {section_name}. Using original content.")
            return text_content

    except Exception as e:
        error_message = str(e)
        if "API key not valid" in error_message or "Authentication error" in error_message:
            st.error("🚨 Gemini API Key Invalid: Please check your API key and try again.")
        elif "quota" in error_message or "rate limit" in error_message:
            st.error("🚨 Gemini API Quota Exceeded or Rate Limited: You've hit your usage limits. Please wait a few minutes and try again, or check your usage on [Google AI Studio](https://makersuite.google.com/app/apikey).")
        elif "404" in error_message and "models/" in error_message:
            st.error(f"🚨 Gemini Model Not Found or Not Supported: The model '{model_name}' might be unavailable or deprecated for your API key. Please try regenerating to select another suitable model or check Google AI Studio for available models.")
        else:
            st.error(f"🚨 An unexpected error occurred during AI enhancement for {section_name}: {e}")
        return text_content