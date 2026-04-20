import streamlit as st
import base64
from pathlib import Path


def _icon_to_data_uri(icon_path: str) -> str:
    icon_file = Path(icon_path)
    if not icon_file.exists():
        return ""

    suffix = icon_file.suffix.lower()
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"
    encoded = base64.b64encode(icon_file.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"

def render_header(page_title: str, page_subtitle: str, icon_path: str, wide: bool = False) -> None:
    icon_src = _icon_to_data_uri(icon_path)
    icon_html = (
        f'<img src="{icon_src}" alt="{page_title} icon" class="opp-header-icon" />'
        if icon_src
        else ""
    )
    header_class = "opp-header opp-header--wide" if wide else "opp-header"

    st.markdown(
        f"""
        <section class="{header_class}">
            <div class="opp-header-main">
                {icon_html}
                <div>
                    <div class="opp-header-kicker">Opportunate</div>
                    <h1 class="opp-header-title">{page_title}</h1>
                    <p class="opp-header-subtitle">{page_subtitle}</p>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )