import streamlit as st
import ui.render_footer as footer
import ui.render_header as header
import ui.theme as theme
from ui.icons import ICON_APP, ICON_HOME, NAV_ITEMS

# Page configuration
st.set_page_config(
    page_title="Opportunate | Home",
    page_icon=ICON_APP,
    layout="centered",
    initial_sidebar_state="collapsed",
)
theme.apply_theme()

# Sidebar configuration
st.sidebar.title("Opportunate")
st.sidebar.caption("Minimal career tools. Pick a workflow below.")

# Header
header.render_header(
    "A Cleaner Path to Your Next Role",
    "Opportunate brings resume intelligence, matching, and role guidance into one calm workspace.",
    ICON_HOME,
    wide=True,
)

# Intro Section
st.subheader("Explore Tools")
st.caption("Each tool solves one step of your job search process.")
st.write("")

tools = [
    (
        item[2],
        item[1],
        item[3],
        {
            "jobradar": "Search jobs across multiple platforms from one screen.",
            "jobmatcher": "Measure how closely your resume matches a target role.",
            "careermatch": "Discover role suggestions based on your extracted profile.",
            "skillbridge": "Find missing skills and map practical next learning steps.",
            "resumebuilder": "Build a polished resume quickly with structured sections.",
            "atstuneup": "Audit ATS readiness with local checks, ML scoring, and AI insights.",
        }[item[0]],
    )
    for item in NAV_ITEMS
    if item[0] != "home"
]

for path, label, icon_path, description in tools:
    nav_col, desc_col = st.columns([0.4, 0.6], vertical_alignment="center", gap="small")
    with nav_col:
        icon_col, link_col = st.columns([0.18, 0.82], vertical_alignment="center", gap="small")
        with icon_col:
            st.image(icon_path, width=20)
        with link_col:
            st.page_link(path, label=label, use_container_width=True)
    with desc_col:
        st.markdown(description)

# Sidebar hint
st.markdown("---")
st.info("Select a tool to get started.")

# Footer
footer.render_footer("home")