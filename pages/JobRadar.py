import streamlit as st  # type: ignore
import ui.render_footer as footer
import ui.render_header as header
import ui.theme as theme
from ui.icons import ICON_APP, ICON_JOBRADAR
import urllib
import urllib.parse

# Page configuration
st.set_page_config(
    page_title="Opportunate | JobRadar",
    page_icon=ICON_APP,
    layout="centered",
    initial_sidebar_state="collapsed",
)
theme.apply_theme()

# Header
header.render_header(
    "JobRadar",
    "Search curated opportunities by role, location, and experience in seconds.",
    ICON_JOBRADAR,
)

# Sidebar configuration
st.sidebar.title("JobRadar")
st.sidebar.caption("Enter your preferences and open listings from top platforms.")

# Main content
st.subheader("Find Open Roles")
st.caption("Fast shortcuts to active listings across multiple job boards.")
st.divider()

cols = st.columns([1, 1], vertical_alignment='center', gap='small')
with cols[0]:
    job = st.text_input("Position / Role", placeholder="eg. Software Engineer")
    location = st.text_input("Preferred Location", value="Pakistan", placeholder="eg. Lahore")
with cols[1]:
    experience = st.selectbox("Years of Experience", ["Fresher", "0-1", "1-3", "3-5", "5+"])
    job_type = st.selectbox("Job Type", ["Any", "Full-time", "Part-time", "Remote", "Hybrid"])
st.write("")

if st.button("Search Jobs", use_container_width=True):
    st.divider()
    job_enc = urllib.parse.quote_plus(job)              # URL-safe job role
    loc_enc = urllib.parse.quote_plus(location)         # URL-safe location

    st.success("Explore jobs from LinkedIn and Indeed:")

    col1, col2 = st.columns(2, gap='small')
    with col1:
        st.image("ui/assets/LinkedIn.png", use_container_width=True)
        st.link_button(
            "LinkedIn",
            f"https://www.linkedin.com/jobs/search/?keywords={job_enc}&location={loc_enc}",
            use_container_width=True,
        )

    with col2:
        st.image("ui/assets/Indeed.png", use_container_width=True)
        st.link_button(
            "Indeed",
            f"https://www.indeed.com/jobs?q={job_enc}&l={loc_enc}",
            use_container_width=True,
        )

# Footer
footer.render_footer("jobradar")