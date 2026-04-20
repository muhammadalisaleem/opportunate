import streamlit as st
from ui.icons import NAV_ITEMS

def render_footer(current_page_key: str) -> None:
    st.divider()
    st.markdown("### Continue in Opportunate")
    nav_cols = st.columns(3, gap="small")

    visible_pages = [item for item in NAV_ITEMS if item[0] != current_page_key]

    for idx, (_, label, path, icon_path) in enumerate(visible_pages):
        with nav_cols[idx % 3]:
            icon_col, link_col = st.columns([0.2, 0.8], vertical_alignment="center", gap="small")
            with icon_col:
                st.image(icon_path, width=18)
            with link_col:
                st.page_link(path, label=label, use_container_width=True)

    st.markdown(
        "<p class='opp-footer-note'>Opportunate • Smart career workflows in one place</p>",
        unsafe_allow_html=True,
    )

    if current_page_key == "home":
        st.markdown("<hr style='border-color: rgba(118, 146, 193, 0.28);'>", unsafe_allow_html=True)
        st.markdown(
            "<p class='opp-footer-note'>made with <3 by Muhammad Ali Saleem</p>",
            unsafe_allow_html=True,
        )