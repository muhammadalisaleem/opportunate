import streamlit as st # type: ignore
import ui.render_footer as footer
import ui.render_header as header
import ui.theme as theme
from ui.icons import ICON_APP, ICON_JOBMATCHER
import preprocessor.parser as parser
from preprocessor.skills import extract_skills_fuzzy, extract_soft_skills_fuzzy, weighted_skill_analysis
from recommender.resources import learning_resources
from preprocessor.spacy_nlp import load_spacy_nlp_model
from analyzer.semantic_matcher import compute_semantic_match_score

# Page configuration
st.set_page_config(
    page_title="Opportunate | JobMatcher",
    page_icon=ICON_APP,
    layout="centered",
    initial_sidebar_state="collapsed",
)
theme.apply_theme()

# Header
header.render_header(
    "JobMatcher",
    "Compare your resume against a specific job description and understand fit clearly.",
    ICON_JOBMATCHER,
)

# Sidebar configuration
st.sidebar.title("JobMatcher")
st.sidebar.caption("Upload your resume and a job description to see compatibility.")

# Main content
st.subheader("Match Your Resume")
st.caption("Understand matched strengths, missing skills, and your overall fit score.")
st.divider()

# Session state setup
if "resume_text_jobmatcher" not in st.session_state:
    st.session_state.resume_text_jobmatcher = None
if "jd_text_jobmatcher" not in st.session_state:
    st.session_state.jd_text_jobmatcher = None

# Resume Upload
st.subheader("Your Resume")
resume_file = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"], key="jobmatcher_resume_uploader")
if resume_file:
    with st.spinner("Processing resume..."):
        file_type = resume_file.type
        if file_type == "application/pdf":
            st.session_state.resume_text_jobmatcher = parser.extract_text_from_pdf(resume_file.read())
        elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            st.session_state.resume_text_jobmatcher = parser.extract_text_from_docx(resume_file.read())
        else:
            st.error("Unsupported resume file type. Please upload a PDF or DOCX.")
            st.session_state.resume_text_jobmatcher = None
            st.stop()
    st.markdown("<br>", unsafe_allow_html=True)
    st.success("Resume processed!")
st.divider()

# Job Description Input
st.subheader("Target Job Description")

# Tabs for JD input method
tab_labels = ["📂 Upload Job Description", "✍️ Paste Job Description"]
if "jobmatcher_jd_tab_selected" not in st.session_state:
    st.session_state.jobmatcher_jd_tab_selected = 0 # Default to upload tab

selected_tab = st.radio("Choose Input Method for Job Description", tab_labels, index=st.session_state.jobmatcher_jd_tab_selected, horizontal=True, key="jobmatcher_jd_input_method_radio")

# Update session state if tab changed
if selected_tab != tab_labels[st.session_state.jobmatcher_jd_tab_selected]:
    st.session_state.jobmatcher_jd_tab_selected = tab_labels.index(selected_tab)
    st.rerun()

jd_text = None
if selected_tab == "📂 Upload Job Description":
    st.write("")
    jd_file = st.file_uploader("Upload the Job Description (PDF or DOCX)", type=["pdf", "docx"], key="jobmatcher_jd_uploader")
    if jd_file:
        with st.spinner("Processing job description..."):
            jd_type = jd_file.type
            if jd_type == "application/pdf":
                jd_text = parser.extract_text_from_pdf(jd_file.read())
            elif jd_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                jd_text = parser.extract_text_from_docx(jd_file.read())
            else:
                st.error("Unsupported job description file type. Please upload a PDF or DOCX.")
                jd_text = None
                st.stop()
        st.markdown("<br>", unsafe_allow_html=True)
        st.success("Job Description processed!")

elif selected_tab == "✍️ Paste Job Description":
    st.write("")
    pasted_text = st.text_area("Paste the Job Description Here:", height=300, key="jobmatcher_jd_pasted_text")
    if pasted_text:
        jd_text = pasted_text


# Main Analysis Logic
if st.session_state.resume_text_jobmatcher and jd_text:
    st.divider()
    st.subheader("Match Analysis Results")

    with st.spinner("Performing match analysis..."):
        nlp = load_spacy_nlp_model()

        resume_doc = nlp(st.session_state.resume_text_jobmatcher)
        jd_doc = nlp(jd_text)

        # Skill Matching
        resume_hard_skills = set(extract_skills_fuzzy(resume_doc))
        resume_soft_skills = set(extract_soft_skills_fuzzy(resume_doc))
        jd_hard_skills_weighted, jd_soft_skills = weighted_skill_analysis(jd_text, nlp)

        # jd_hard_skills_weighted is a dictionary, so .keys() is appropriate here
        jd_hard_skills = set(jd_hard_skills_weighted.keys())

        matched_hard_skills = resume_hard_skills.intersection(jd_hard_skills)
        missing_hard_skills = jd_hard_skills.difference(resume_hard_skills)
        matched_soft_skills = resume_soft_skills.intersection(jd_soft_skills)
        missing_soft_skills = jd_soft_skills.difference(resume_soft_skills)

        # Score Generation
        total_jd_hard_weight = sum(jd_hard_skills_weighted.values())
        matched_hard_weight = sum(jd_hard_skills_weighted[s] for s in matched_hard_skills)

        hard_pct = (matched_hard_weight / total_jd_hard_weight) * 100 if total_jd_hard_weight else 0
        soft_pct = (len(matched_soft_skills) / len(jd_soft_skills)) * 100 if jd_soft_skills else 0

        semantic_pct, semantic_available, semantic_error = compute_semantic_match_score(
            st.session_state.resume_text_jobmatcher,
            jd_text,
        )

        # Blend rule-based and embedding-based scoring when the model is available.
        if semantic_available:
            hard_score_contribution = hard_pct * 0.7 # Hard skills contribute 70%
            soft_score_contribution = soft_pct * 0.1 # Soft skills contribute 10%
            semantic_score_contribution = semantic_pct * 0.2 # Semantic similarity contributes 20%
        else:
            hard_score_contribution = hard_pct * 0.9 # Hard skills contribute 90%
            soft_score_contribution = soft_pct * 0.1 # Soft skills contribute 10%
            semantic_score_contribution = 0

        final_score = round(hard_score_contribution + soft_score_contribution + semantic_score_contribution)

        # Categorize hard skills for display
        def categorize(skills_dict):
            core, imp, opt = [], [], []
            for s, w in skills_dict.items():
                if w >= 2.5: core.append(s)
                elif w >= 1.0: imp.append(s)
                else: opt.append(s)
            return sorted(core), sorted(imp), sorted(opt)

        matched_hard_core, matched_hard_imp, matched_hard_opt = categorize(
            {s: jd_hard_skills_weighted[s] for s in matched_hard_skills}
        )
        missing_hard_core, missing_hard_imp, missing_hard_opt = categorize(
            {s: jd_hard_skills_weighted[s] for s in missing_hard_skills}
        )

        # Display Results
        st.header("📊 Job Compatibility Score")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### Overall Compatibility: <span style='font-weight:normal'>{final_score}%</span>", unsafe_allow_html=True)
        st.progress(final_score / 100)
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"### 🧱 Hard Skills Match: <span style='font-weight:normal'>{round(hard_pct)}% of 90 → {round(hard_score_contribution)} points</span>", unsafe_allow_html=True)
        st.markdown(f"### 🎭 Soft Skills Match: <span style='font-weight:normal'>{round(soft_pct)}% of 10 → {round(soft_score_contribution)} points</span>", unsafe_allow_html=True)
        if semantic_available:
            st.markdown(f"### 🧠 Semantic Match: <span style='font-weight:normal'>{round(semantic_pct)}% of 20 → {round(semantic_score_contribution)} points</span>", unsafe_allow_html=True)
        if semantic_error:
            st.caption(f"Semantic matching fallback active: {semantic_error}")
        st.write("")
        st.divider()

        def show_skills_section(label, badge_color, core_skills, important_skills, optional_skills):
            st.subheader(label)
            st.markdown("<br>", unsafe_allow_html=True)
            if core_skills:
                st.markdown(f"##### 🔐 Core Skills: " + " ".join(f":{badge_color}-badge[{s.title()}]" for s in core_skills))
            if important_skills:
                st.markdown(f"##### 💡 Important Skills: " + " ".join(f":{badge_color}-badge[{s.title()}]" for s in important_skills))
            if optional_skills:
                st.markdown(f"##### 🧩 Nice-to-Have Skills: " + " ".join(f":{badge_color}-badge[{s.title()}]" for s in optional_skills))
            if not (core_skills or important_skills or optional_skills):
                st.info(f"No {label.lower().replace('skills', '')} hard skills.")

        # Matched Skills
        st.subheader("✅ Matched Skills")
        st.markdown("<br>", unsafe_allow_html=True)
        show_skills_section("Hard Skills", "green", matched_hard_core, matched_hard_imp, matched_hard_opt)
        if matched_soft_skills:
            st.markdown(f"##### Soft Skills: " + " ".join(f":green-badge[{s.title()}]" for s in sorted(matched_soft_skills)))
        elif not matched_soft_skills:
            st.write("")
            st.info("No matched soft skills.")
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # Missing Skills
        st.subheader("❌ Missing Skills")
        st.markdown("<br>", unsafe_allow_html=True)
        show_skills_section("Hard Skills", "red", missing_hard_core, missing_hard_imp, missing_hard_opt)
        if missing_soft_skills:
            st.markdown(f"##### Soft Skills: " + " ".join(f":red-badge[{s.title()}]" for s in sorted(missing_soft_skills)))
        elif not missing_soft_skills:
            st.success("No missing soft skills!")
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # Overall recommendation based on score
        if final_score >= 80:
            st.success("✅ Excellent Match! Your resume is highly compatible with this job description. Focus on interview preparation!")
        elif final_score >= 65:
            st.info("✨ Good Match! You're a solid fit. Review the missing skills and consider tailoring your resume further.")
        else:
            st.warning("⚠️ Needs Improvement. There's a significant skill gap. Focus on developing the missing skills or tailoring your resume more intensely.")

        # Learning resources for missing skills
        st.divider()
        st.header("📚 Recommended Resources for Missing Skills")
        st.write("")
        all_missing_skills = list(missing_hard_skills) + list(missing_soft_skills)
        if all_missing_skills:
            learning_resources(all_missing_skills)
        else:
            st.info("You've got all the essential skills covered for this role!")


# Footer
footer.render_footer("jobmatcher")