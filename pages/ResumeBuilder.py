import streamlit as st  # type: ignore
from builder import form_inputs, generator_standard, resume_enhancer
import ui.render_footer as footer
import ui.render_header as header
import ui.theme as theme
from ui.icons import ICON_APP, ICON_RESUMEBUILDER
import re
from io import BytesIO
import time # Import the time module for delays

# Page configuration
st.set_page_config(
    page_title="Opportunate | ResumeBuilder",
    page_icon=ICON_APP,
    layout="centered",
    initial_sidebar_state="collapsed",
)
theme.apply_theme()

# Header
header.render_header(
    "ResumeBuilder",
    "Create a clean, ATS-friendly resume with optional AI enhancement.",
    ICON_RESUMEBUILDER,
)

# Sidebar configuration
st.sidebar.title("ResumeBuilder")
st.sidebar.caption("Fill your details and generate a polished resume draft.")

# Main content
st.subheader("Build Your Resume")
st.caption("Structured sections with optional AI polishing for stronger wording.")
st.divider()

# Step 1: Ask how many entries user wants to give
st.header("📌 Entry Counts for Sections")
st.write("")
col1, col2 = st.columns([1, 1], gap="small", vertical_alignment="center")
with col1:
    num_edu = st.number_input("How many education entries?", 0, 10, 1, key="edu_count")
    num_proj = st.number_input("How many projects?", 0, 10, 1, key="proj_count")
with col2:
    num_exp = st.number_input("How many work experiences?", 0, 10, 1, key="exp_count")
    num_cert = st.number_input("How many certifications?", 0, 10, 1, key="cert_count")
st.divider()

# Gemini API Key Input and Tone Control
st.header("🤖 AI Enhancement Options")
st.write("")
gemini_api_key = resume_enhancer.get_gemini_api_key() # Get API key using the enhancer module
st.write("")
selected_tone = st.selectbox(
    "Select Enhancement Tone:",
    ["Professional", "Executive", "Technical", "Creative"],
    key="ai_tone_select",
    help="Choose the tone for AI-enhanced sections (Summary, Responsibilities, Projects, Skills, Achievements)."
)
st.divider()

# Display dynamic form based on counts
st.header("✒️ Your Details")
st.write("")
with st.form("resume_form"):
    personal = form_inputs.personal_section()
    summary = form_inputs.summary_section()
    education = form_inputs.education_section(num_edu) if num_edu > 0 else []
    experience = form_inputs.experience_section(num_exp) if num_exp > 0 else []
    projects = form_inputs.project_section(num_proj) if num_proj > 0 else []
    skills = form_inputs.skills_section()
    certifications = form_inputs.certification_section(num_cert) if num_cert > 0 else []
    extras = form_inputs.additional_section()

    col_buttons = st.columns(2)
    with col_buttons[0]:
        generate_standard = st.form_submit_button("✅ Generate Resume", use_container_width=True)
    with col_buttons[1]:
        generate_ai_enhanced = st.form_submit_button("✨ Generate AI-Enhanced Resume", use_container_width=True)

# Validation logic before rendering resume
if generate_standard or generate_ai_enhanced:
    errors = []
    warnings = []

    # Personal Info Check
    if not personal["name"].strip():
        errors.append("❌ Full Name is required.")
    if not personal["email"].strip():
        errors.append("❌ Email is required.")
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", personal["email"]):
        errors.append("❌ Email format is invalid.")
    if not personal["phone"].strip():
        errors.append("❌ Phone Number is required.")
    if not personal["location"].strip():
        warnings.append("⚠️ Adding your Location is recommended.")
    if not personal["linkedin"].strip():
        warnings.append("⚠️ Adding LinkedIn URL is recommended.")
    if not personal["github"].strip():
        warnings.append("⚠️ Adding GitHub URL is recommended.")
    if not personal["website"].strip():
        warnings.append("⚠️ Adding Personal Website URL is recommended.")

    # Summary Check
    if not summary.strip():
        errors.append("❌ Professional Summary is required.")

    # Education Check
    for i in range (num_edu):
        if not education[i]["university"]:
            errors.append(f"❌ University {i + 1} is required.")
        if not education[i]["degree"]:
            errors.append(f"❌ Degree {i + 1} is required.")
        if not education[i]["end_date"]:
            errors.append(f"❌ End Date {i + 1} is required.")
        if not education[i]["gpa"]:
            warnings.append(f"⚠️ Adding GPA {i + 1} is recommended.")
        if not education[i]["coursework"].strip():
            warnings.append(f"⚠️ Adding Coursework {i + 1} is recommended.")

    # Work Experience Check
    for i in range (num_exp):
        if not experience[i]["job_title"]:
            errors.append(f"❌ Job {i + 1} Title is required.")
        if not experience[i]["company"]:
            errors.append(f"❌ Company {i + 1} is required.")
        if not experience[i]["end_date"]:
            errors.append(f"❌ Job {i + 1} End Date is required.")
        if not experience[i]["responsibilities"]:
            warnings.append(f"⚠️ Adding Job Responsibilities and Challenges {i + 1} is recommended.")
    
    # Project Check
    for i in range (num_proj):
        if not projects[i]["title"]:
            errors.append(f"❌ Project {i + 1} Title is required.")
        if not projects[i]["tech_stack"]:
            warnings.append(f"⚠️ Adding Project {i + 1} Tech Stack is recommended.")
        if not projects[i]["link"]:
            warnings.append(f"⚠️ Adding Repository Link {i + 1} is recommended.")
        if not projects[i]["deployment"]:
            warnings.append(f"⚠️ Adding your Deployment Link {i + 1} is recommended.")
        if not projects[i]["description"].strip():
            errors.append(f"❌ Project {i + 1} Description is required.")

    # Skills Check
    if len(skills["technical"]) + len(skills["soft"]) == 0:
        errors.append("❌ Please enter at least one skill (technical or soft).")
    elif len(skills["technical"]) <= 4:
        warnings.append("⚠️ Adding more Technical Skills is recommended.")
    elif len(skills["soft"]) <= 2:
        warnings.append("⚠️ Adding more Soft Skills is recommended.")
    
    # Certification Check
    for i in range (num_cert):
        if not certifications[i]["title"]:
            errors.append(f"❌ Certification {i + 1} Title is required.")
        if not certifications[i]["issuer"]:
            warnings.append(f"⚠️ Adding Certification {i + 1} Issuer is recommended.")
        if not certifications[i]["link"]:
            warnings.append(f"⚠️ Adding Certification {i + 1} Link is recommended.")

    # Experience/project validation if count > 0
    if num_exp > 0 and not experience:
        errors.append("❌ You chose to add experience, but provided no entries.")
    if num_proj > 0 and not projects:
        errors.append("❌ You chose to add projects, but provided no entries.")

    # Display errors
    if errors and warnings:
        st.markdown("<br>", unsafe_allow_html=True)
        st.error("Please fix the following before generating your resume:\n\n" + "\n\n".join(f"{e}" for e in errors))
        st.write("")
        st.warning("Please consider adding the following for an ATS-friendly resume:\n\n" + "\n\n".join(f"{w}" for w in warnings))
    elif warnings:
        st.markdown("<br>", unsafe_allow_html=True)
        st.warning("Please consider adding the following for an ATS-friendly resume:\n\n" + "\n\n".join(f"{w}" for w in warnings))
    elif errors:
        st.markdown("<br>", unsafe_allow_html=True)
        st.error("Please fix the following before generating your resume:\n\n" + "\n\n".join(f"{e}" for e in errors))
        st.stop()

    if not errors:
        st.divider()
        with st.spinner("AI is enhancing your resume... This might take a moment."):
            processed_personal = personal
            processed_summary = summary
            processed_education = education
            processed_skills = skills
            processed_certifications = certifications
            processed_extras = extras
            processed_experience = []
            processed_projects = []

            # Check if AI enhancement is requested but API key is missing
            if generate_ai_enhanced and not gemini_api_key:
                st.warning("No Gemini API key provided. An unenhanced resume will be generated.")
                generate_ai_enhanced = False # Disable enhancement for this run

            # Process Summary
            if generate_ai_enhanced and gemini_api_key and summary:
                processed_summary = resume_enhancer.enhance_content_with_gemini(
                    "professional summary", summary, selected_tone, gemini_api_key
                )
                time.sleep(3) # Add delay to respect API rate limits

            # Process Work Experience
            for i, exp_entry in enumerate(experience):
                current_exp = exp_entry.copy()
                
                if generate_ai_enhanced and gemini_api_key and experience[i]:
                    enhanced_resp_text = resume_enhancer.enhance_content_with_gemini(
                        "job responsibility", "\n".join(current_exp["responsibilities"]), selected_tone, gemini_api_key
                    )
                    current_exp["responsibilities"] = [line.strip() for line in enhanced_resp_text.split('\n') if line.strip()] 
                elif isinstance(current_exp["responsibilities"], list):
                    current_exp["responsibilities"] = [r.strip() for r in current_exp["responsibilities"] if r.strip()] # Clean list elements
                
                processed_experience.append(current_exp)
                if generate_ai_enhanced and gemini_api_key:
                    time.sleep(3) # Add delay after each experience enhancement

            # Process Projects
            for i, proj_entry in enumerate(projects):
                current_proj = proj_entry.copy()

                if generate_ai_enhanced and gemini_api_key and projects[i]:
                    enhanced_desc_text = resume_enhancer.enhance_content_with_gemini(
                        "project description", current_proj["description"], selected_tone, gemini_api_key
                    )
                    current_proj["description"] = [line.strip() for line in enhanced_desc_text.split('\n') if line.strip()]
                elif isinstance(current_proj["description"], str):
                    current_proj["description"] = [line.strip() for line in current_proj["description"].split('\n') if line.strip()]

                processed_projects.append(current_proj)
                if generate_ai_enhanced and gemini_api_key:
                    time.sleep(3) # Add delay after each project enhancement

            # Process Skills
            if generate_ai_enhanced and gemini_api_key and skills:
                # Combine technical and soft skills into a single string for enhancement
                all_skills_text = ", ".join(skills["technical"] + skills["soft"])
                enhanced_skills_string = resume_enhancer.enhance_content_with_gemini(
                    "skills section", all_skills_text, selected_tone, gemini_api_key
                )
                # Parse the specific output format: "Technical Skills: ..., Soft Skills: ..."
                tech_skills = []
                soft_skills = []
                lines = enhanced_skills_string.split('\n')
                for line in lines:
                    if line.startswith("Technical Skills:"):
                        tech_str = line.replace("Technical Skills:", "").strip()
                        tech_skills = [s.strip() for s in tech_str.split(',') if s.strip()]
                    elif line.startswith("Soft Skills:"):
                        soft_str = line.replace("Soft Skills:", "").strip()
                        soft_skills = [s.strip() for s in soft_str.split(',') if s.strip()]
                
                processed_skills = {"technical": tech_skills, "soft": soft_skills}
                time.sleep(3) # Add delay after skills enhancement
            else:
                # Ensure skills are lists for generator
                processed_skills["technical"] = [s.strip() for s in processed_skills["technical"] if s.strip()]
                processed_skills["soft"] = [s.strip() for s in processed_skills["soft"] if s.strip()]


            # Process Achievements
            if generate_ai_enhanced and gemini_api_key and extras["achievements"]:
                # Join all achievements into a single string for enhancement
                all_achievements_text = "\n".join(extras["achievements"])
                enhanced_achievements_string = resume_enhancer.enhance_content_with_gemini(
                    "achievements", all_achievements_text, selected_tone, gemini_api_key
                )
                processed_extras["achievements"] = [a.strip() for a in enhanced_achievements_string.split(',') if a.strip()]
            else:
                processed_extras["achievements"] = [a.strip() for a in processed_extras["achievements"] if a.strip()]


        # Assemble data dictionary for generator
        data = {
            "personal": processed_personal,
            "summary": processed_summary,
            "education": processed_education,
            "experience": processed_experience,
            "projects": processed_projects,
            "skills": processed_skills,
            "certifications": processed_certifications,
            "achievements_hobbies": processed_extras
        }

        # Generate and display resume
        try:
            docx_buffer = generator_standard.generate_structured_resume(data, "data/template.docx")
            
            if warnings:
                st.write("")
                st.success("Resume generated successfully!")
                st.info("Please note the following recommendations:\n\n" + "\n\n".join(f"{w}" for w in warnings))
            else:
                st.markdown("<br>", unsafe_allow_html=True)
                st.success("Resume generated successfully!")
            
            if generate_ai_enhanced:
                st.info("Kindly review your resume thoroughly if generated using AI. Sometimes it may add unrealistic or false statistics which should be ethically removed from the resume.")

            st.divider()
            st.write("")
            st.download_button(
                label="Download Resume (DOCX)",
                data=docx_buffer.getvalue(),
                file_name=f"{personal['name'].replace(' ', '_')}_Resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        except Exception as e:
            if warnings:
                st.write("")
                st.error(f"An error occurred during resume generation: {e}")
                st.info("This might be due to an issue with the template or data format. Please review your inputs or contact support.")
            else:
                st.markdown("<br>", unsafe_allow_html=True)
                st.error(f"An error occurred during resume generation: {e}")
                st.info("This might be due to an issue with the template or data format. Please review your inputs or contact support.")

# Footer
footer.render_footer("resumebuilder")