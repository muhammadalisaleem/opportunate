import streamlit as st

def get_youtube_link(skill: str) -> str:
    query = skill.replace(" ", "+")
    return f"https://www.youtube.com/results?search_query={query}+tutorial"

def get_udemy_link(skill: str) -> str:
    query = skill.replace(" ", "+")
    return f"https://www.udemy.com/courses/search/?q={query}&sort=popularity"

def get_coursera_link(skill: str) -> str:
    query = skill.replace(" ", "+")
    return f"https://www.coursera.org/search?query={query}&sort=POPULARITY"

def get_edX_link(skill: str) -> str:
    query = skill.replace(" ", "+")
    return f"https://www.edx.org/search?q={query}"

def learning_resources(missing_skills):
    st.markdown("<br>", unsafe_allow_html=True)
    selected_skill = st.selectbox("Pick a missing skill to explore:", sorted(missing_skills), index=None, placeholder="Select Skill")
    st.markdown("<br><br>", unsafe_allow_html=True)

    if selected_skill:
        yt_url = get_youtube_link(selected_skill)
        udemy_url = get_udemy_link(selected_skill)
        coursera_url = get_coursera_link(selected_skill)
        edX_url = get_edX_link(selected_skill)

        col1, col2 = st.columns(2)
        with col1:
            st.image("ui/assets/youtube.png", use_container_width=True)
            st.link_button(f"▶️ Learn {selected_skill} on YouTube", yt_url, use_container_width=True)
        
            st.markdown("<br>", unsafe_allow_html=True)

            st.image("ui/assets/coursera.png", use_container_width=True)
            st.link_button(f"📘 Learn {selected_skill} on Coursera", coursera_url, use_container_width=True)
        
        with col2:
            st.image("ui/assets/udemy.png", use_container_width=True)
            st.link_button(f"🎓 Learn {selected_skill} on Udemy", udemy_url, use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            st.image("ui/assets/edx.png", use_container_width=True)
            st.link_button(f"💡 Learn {selected_skill} on edX", edX_url, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("You can also refer to articles on credible websites like GeeksforGeeks, W3Schools, and Javatpoint.")