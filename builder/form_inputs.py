import streamlit as st

def personal_section():
    with st.expander("👤 Personal Information"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *")
            email = st.text_input("Email *")
            location = st.text_input("Location (Recommended)")
            linkedin = st.text_input("LinkedIn URL (Recommended)")
        with col2:
            title = st.text_input("Professional Title")
            phone = st.text_input("Phone Number *")
            website = st.text_input("Portfolio Website (Recommended)")
            github = st.text_input("GitHub URL (Recommended)")
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin": linkedin,
        "github": github,
        "website": website,
        "title": title
    }

def summary_section():
    with st.expander("📝 Summary"):
        summary = st.text_area("Professional Summary *")
    return summary

def education_section(count):
    entries = []
    with st.expander("🎓 Education"):
        for i in range(count):
            st.write("")
            st.markdown(f"#### Education {i + 1}")
            col1, col2 = st.columns(2)
            with col1:
                university = st.text_input(f"University *", key=f"edu_uni_{i}")
                location = st.text_input("Location", key=f"edu_loc_{i}")
                start_date = st.text_input("Start Date", key=f"edu_sdate_{i}")
            with col2:
                degree = st.text_input(f"Degree *", key=f"edu_degree_{i}")
                gpa = st.text_input("GPA (Recommended)", key=f"edu_gpa_{i}")
                end_date = st.text_input("End Date *", key=f"edu_edate_{i}")
            coursework = st.text_area("Relevant Coursework (Recommended)", key=f"edu_course_{i}")
            entries.append({
                "degree": degree,
                "university": university,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "gpa": gpa,
                "coursework": coursework
            })
    return entries

def experience_section(count):
    entries = []
    with st.expander("💼 Work Experience"):
        for i in range(count):
            st.write("")
            st.markdown(f"#### Work Experience {i + 1}")
            job_title = st.text_input("Job Title *", key=f"exp_title_{i}")
            col1, col2 = st.columns(2)
            with col1:
                company = st.text_input("Company *", key=f"exp_company_{i}")
                start_date = st.text_input("Start Date", key=f"exp_sdate_{i}")
            with col2:
                location = st.text_input("Location", key=f"exp_loc_{i}")
                end_date = st.text_input("End Date *", key=f"exp_edate_{i}")
            responsibilities = st.text_area("Responsibilities (one per line) (Recommended)", key=f"exp_resp_{i}").splitlines()
            entries.append({
                "job_title": job_title,
                "company": company,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "responsibilities": responsibilities
            })
    return entries

def project_section(count):
    entries = []
    with st.expander("🛠️ Projects"):
        for i in range(count):
            st.write("")
            st.markdown(f"#### Project {i + 1}")
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Project Title *", key=f"proj_title_{i}")
                tech_stack = st.text_input("Tech Stack", key=f"proj_tech_{i}")
            with col2:
                deployment = st.text_input("Deployment Link (Recommended)", key=f"proj_deploy_{i}")
                link = st.text_input("GitHub Link (Recommended)", key=f"proj_link_{i}")
            description = st.text_area("Description *", key=f"proj_desc_{i}")
            entries.append({
                "title": title,
                "tech_stack": tech_stack,
                "deployment": deployment,
                "link": link,
                "description": description
            })
    return entries

def skills_section():
    with st.expander("🧠 Skills"):
        hard_skills = st.text_area("Hard Skills (comma or line separated)").replace("\n", ",").split(",")
        soft_skills = st.text_area("Soft Skills (comma or line separated)").replace("\n", ",").split(",")
    return {
        "technical": [h.strip() for h in hard_skills if h.strip()],
        "soft": [s.strip() for s in soft_skills if s.strip()]
    }

def certification_section(count):
    entries = []
    with st.expander("📜 Certifications"):
        for i in range(count):
            st.write("")
            st.markdown(f"#### Certificate {i + 1}")
            title = st.text_input("Certificate Title*", key=f"cert_title_{i}")
            col1, col2 = st.columns(2)
            with col1:
                issuer = st.text_input("Issued By", key=f"cert_issuer_{i}")
            with col2:
                link = st.text_input("Certificate Link (Recommended)", key=f"cert_link_{i}")
            entries.append({
                "title": title,
                "issuer": issuer,
                "link": link
            })
    return entries

def additional_section():
    with st.expander("🏆 Achievements & Hobbies"):
        achievements = st.text_area("Achievements (comma or line separated)").replace("\n", ",").split(",")
        hobbies = st.text_area("Hobbies (comma or line separated)").replace("\n", ",").split(",")
    return {
        "achievements": [a.strip() for a in achievements if a.strip()],
        "hobbies": [h.strip() for h in hobbies if h.strip()]
    }
