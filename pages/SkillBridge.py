import streamlit as st # type: ignore
import ui.render_footer as footer
import ui.render_header as header
import ui.theme as theme
from ui.icons import ICON_APP, ICON_SKILLBRIDGE
import json
import preprocessor.parser as parser
from preprocessor.skills import extract_skills_fuzzy
from recommender.resources import learning_resources
from recommender.skill_gap_ranker import rank_missing_skills
from preprocessor.spacy_nlp import load_spacy_nlp_model

# Page configuration
st.set_page_config(
    page_title="Opportunate | SkillBridge",
    page_icon=ICON_APP,
    layout="centered",
    initial_sidebar_state="collapsed",
)
theme.apply_theme()

# Header
header.render_header(
    "SkillBridge",
    "See your skill gaps for a target role and get a focused roadmap to close them.",
    ICON_SKILLBRIDGE,
)

# Sidebar configuration
st.sidebar.title("SkillBridge")
st.sidebar.caption("Upload your resume, choose a role, and view missing skills.")

# Main content
st.subheader("Bridge the Gap")
st.caption("Measure matched skills and prioritize what to learn next.")
st.divider()

resume_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

# Load Job Roles
@st.cache_data
def load_job_roles():
    with open("data/dataset/job_to_skill.json", "r") as f:
        return json.load(f)

job_skills_map = load_job_roles()
available_roles = sorted(job_skills_map.keys())

# Resume Extraction and Analysis
if resume_file:
    with st.spinner("Analyzing your resume and extracting skills..."):
        if resume_file.type == "application/pdf":
            resume_text = parser.extract_text_from_pdf(resume_file.read())
        elif resume_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            resume_text = parser.extract_text_from_docx(resume_file.read())
        else:
            st.error("Unsupported file type. Please upload a PDF or DOCX.")
            st.stop()
        
        # Load the SpaCy model using the cached function
        nlp = load_spacy_nlp_model()

        resume_doc = nlp(resume_text)
        extracted_skills = set(extract_skills_fuzzy(resume_doc))

    # Role Selection
    st.divider()
    selected_role = st.selectbox("Select a target job role:", available_roles)
    if selected_role:
        required_skills = set(job_skills_map[selected_role])
        matched_skills = extracted_skills & required_skills
        missing_skills = required_skills - extracted_skills
        ranked_missing_skills = rank_missing_skills(
            selected_role,
            sorted(extracted_skills),
            candidate_skills=sorted(missing_skills),
            top_n=len(missing_skills),
        )
        ranked_missing_skill_names = [item["skill"] for item in ranked_missing_skills]

        if ranked_missing_skill_names:
            ordered_missing_skills = [skill for skill in ranked_missing_skill_names if skill in missing_skills]
            ordered_missing_skills.extend([skill for skill in sorted(missing_skills) if skill not in ordered_missing_skills])
        else:
            ordered_missing_skills = sorted(missing_skills)

        st.divider()
        st.markdown(f"## 🎯 Skill Match for: {selected_role}")
        st.markdown("<br><br>", unsafe_allow_html=True)

        st.markdown(f"#### ✅ Matched Skills: <span style='font-weight:normal'>({len(matched_skills)}/{len(required_skills)})</span>", unsafe_allow_html=True)
        st.markdown("#### " + " ".join(f":green-badge[{skill}]" for skill in sorted(matched_skills)) or "_None_")
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"#### 💡 Recommended Additional Skills: <span style='font-weight:normal'>({len(missing_skills)} skill{'s' if len(missing_skills) != 1 else ''})</span>", unsafe_allow_html=True)
        st.markdown("#### " + " ".join(f":blue-badge[{skill}]" for skill in ordered_missing_skills) or "_None_")

        if ranked_missing_skills:
            st.markdown("### 🤖 AI-Ranked Skill Gaps")
            for item in ranked_missing_skills:
                st.markdown(
                    f"- **{item['skill']}** — score {item['score']}% "
                    f"(model {item['model_probability']}%, semantic {item['semantic_similarity']}%)"
                )

        st.divider()
        if missing_skills:
            st.markdown("### 📚 Recommended Resources for Additional Skills")
            learning_resources(ordered_missing_skills)
        else:
            st.success("You're fully equipped for this role! 💼")
# Footer
footer.render_footer("skillbridge")