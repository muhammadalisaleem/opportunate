import streamlit as st
import ui.render_footer as footer
import ui.render_header as header
import ui.theme as theme
from ui.icons import ICON_APP, ICON_ATSTUNEUP
from analyzer.analysis_enhancer import (
    get_gemini_api_key,
    perform_ai_ats_analysis
)
from analyzer.resume_analysis import run_local_ats_analysis
from analyzer.ats_score_model import predict_score
from preprocessor.parser import extract_text_from_uploaded_file

# Page configuration
st.set_page_config(
    page_title="Opportunate | ATS TuneUp",
    page_icon=ICON_APP,
    layout="centered",
    initial_sidebar_state="collapsed",
)
theme.apply_theme()

# Header
header.render_header(
    "ATS TuneUp",
    "Evaluate resume ATS readiness using rule-based checks, ML scoring, and AI review.",
    ICON_ATSTUNEUP,
)

# Sidebar
st.sidebar.title("ATS TuneUp")
st.sidebar.caption("Upload a resume and run local, ML, or AI ATS analysis.")

# Title
st.subheader("Tune Your Resume")
st.caption("Spot weaknesses and improve ATS compatibility with focused feedback.")
st.divider()

# Upload Section
uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
st.write("")

# AI Key Input Section
api_key = get_gemini_api_key()

# Buttons
col1, col2, col3 = st.columns([1, 1, 1])
run_local = col1.button("🔍 ATS Analysis", use_container_width=True)
run_ml = col2.button("🤖 ML ATS Score", use_container_width=True)
run_ai = col3.button("✨ AI Enhanced Analysis", use_container_width=True)

if uploaded_file:
    resume_text = extract_text_from_uploaded_file(uploaded_file)

    if run_ml:
        st.divider()
        st.subheader("🤖 ML ATS Score Results")
        st.write("")
        with st.spinner("Scoring resume with the trained ATS model..."):
            ats_score, meta = predict_score(resume_text, uploaded_file)

            if not meta.get("available"):
                st.warning(meta.get("reason", "ATS score model is unavailable."))
            else:
                st.markdown(f"### 🧠 Predicted ATS Score: **{round(ats_score)}/100**")
                st.progress(min(int(round(ats_score)), 100), text="ML ATS Score")

                if ats_score >= 80:
                    st.success("Excellent ATS profile. This resume has strong structural and content signals.")
                elif ats_score >= 60:
                    st.info("Good ATS profile. There is room to improve section quality and keyword density.")
                else:
                    st.warning("Needs improvement. The model sees weak ATS signals in this resume.")

                features = meta.get("features", {})
                st.markdown("#### Feature Snapshot")
                st.write({
                    "word_count": features.get("word_count"),
                    "bullet_count": features.get("bullet_count"),
                    "quantified_items": features.get("quant_count"),
                    "skill_count": features.get("skill_count"),
                    "experience_years": features.get("experience_years"),
                    "certification_count": features.get("cert_count"),
                    "education_rank": features.get("education_rank"),
                })

    if run_local:
        st.divider()
        st.subheader("🔍 ATS Analysis Results")
        st.write("")
        with st.spinner("Analyzing resume..."):
            local_feedback = run_local_ats_analysis(resume_text, uploaded_file)
            for step in local_feedback:
                st.markdown(f"### 🧩 Step {step['step']}: {step['title']}")
                for level, msg in step["findings"]:
                    if level == "warning":
                        st.warning(msg)
                    else:
                        st.success(msg)
            
            st.divider()
            st.write("")
            st.info("""We recommend the use of other online ATS Analysis tools as sometimes some tools provide new insights that the others do not. Some of the recommended tools are listed below:""")
            cols = st.columns([1, 1, 1], vertical_alignment='center', gap='small')
            with cols[0]:
                st.link_button("Weekday", "https://www.weekday.works/resume-checker-and-scoring-tool", use_container_width= True)
                st.link_button("MyPerfectResume", "https://www.myperfectresume.com/resume/ats-resume-checker", use_container_width= True)
            with cols[1]:
                st.link_button("Resume-Now", "https://www.resume-now.com/build-resume?mode=ats", use_container_width= True)
                st.link_button("Enhancv", "https://enhancv.com/resources/resume-checker/", use_container_width= True)
            with cols[2]:
                st.link_button("Jobscan", "https://www.jobscan.co/", use_container_width= True)
                st.link_button("1MillionResume", "https://1millionresume.com/resume-checker", use_container_width= True)

    elif run_ai:
        st.divider()
        if not api_key:
            st.error("Please enter your Google Gemini API key to use AI-based analysis.")
        else:
            st.subheader("✨ AI Enhanced ATS Analysis")
            st.write("")
            with st.spinner("AI is reviewing your resume..."):
                ai_feedback = perform_ai_ats_analysis(resume_text, api_key)

                # Display ATS score if present
                ats_score = ai_feedback.get("ATS_Score")
                if ats_score is not None:
                    st.markdown(f"### 🧠 ATS Compatibility Score: **{ats_score}/100**")
                    st.progress(min(int(ats_score), 100), text = "ATS Score")
                    if ats_score >= 80:
                        st.success("Excellent! Your resume is highly ATS-compatible.")
                    elif ats_score >= 60:
                        st.info("Good, but there's room for improvement.")
                    else:
                        st.warning("Needs improvement. Follow the suggestions below.")

                # Render all category feedback
                for category, results in ai_feedback.items():
                    if category == "ATS_Score":
                        continue
                    st.markdown(f"### 🎗️ {category}")
                    positives = results.get("Positives", [])
                    negatives = results.get("Negatives", [])
                    for pos in positives:
                        st.success(pos)
                    for neg in negatives:
                        st.warning(neg)
                
                st.divider()
                st.write("")
                st.info("""We recommend the use of other online ATS Analysis tools as sometimes some tools provide new insights that the others do not. Some of the recommended tools are listed below:""")
                cols = st.columns([1, 1, 1], vertical_alignment='center', gap='small')
                with cols[0]:
                    st.link_button("Weekday", "https://www.weekday.works/resume-checker-and-scoring-tool", use_container_width= True)
                    st.link_button("MyPerfectResume", "https://www.myperfectresume.com/resume/ats-resume-checker", use_container_width= True)
                with cols[1]:
                    st.link_button("Resume-Now", "https://www.resume-now.com/build-resume?mode=ats", use_container_width= True)
                    st.link_button("Enhancv", "https://enhancv.com/resources/resume-checker/", use_container_width= True)
                with cols[2]:
                    st.link_button("Jobscan", "https://www.jobscan.co/", use_container_width= True)
                    st.link_button("1MillionResume", "https://1millionresume.com/resume-checker", use_container_width= True)
else:
    st.info("Please upload your resume above to begin analysis.")

# Footer
footer.render_footer("atstuneup")