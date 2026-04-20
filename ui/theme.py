import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

            :root {
                --opp-bg-start: #081225;
                --opp-bg-end: #0d1c38;
                --opp-surface: rgba(16, 32, 61, 0.72);
                --opp-border: rgba(118, 146, 193, 0.28);
                --opp-text: #e8f0ff;
                --opp-muted: #a9bada;
                --opp-accent: #4cc9f0;
                --opp-accent-soft: rgba(76, 201, 240, 0.18);
            }

            .stApp {
                background:
                    radial-gradient(circle at 85% 10%, rgba(76, 201, 240, 0.14) 0%, rgba(76, 201, 240, 0) 45%),
                    linear-gradient(160deg, var(--opp-bg-start) 0%, var(--opp-bg-end) 100%);
                color: var(--opp-text);
                font-family: 'Manrope', sans-serif;
            }

            [data-testid='stSidebar'] {
                background: rgba(8, 18, 37, 0.92);
                border-right: 1px solid var(--opp-border);
            }

            h1, h2, h3, h4 {
                font-family: 'Space Grotesk', sans-serif;
                letter-spacing: -0.02em;
                color: var(--opp-text);
            }

            p, label, .stCaption, .stMarkdown {
                color: var(--opp-muted);
            }

            .stMetricLabel,
            .stMetricValue,
            .st-emotion-cache-16txtl3,
            .st-emotion-cache-10trblm,
            .st-emotion-cache-1wivap2,
            [data-testid='stFileUploader'] label,
            [data-testid='stWidgetLabel'] {
                color: var(--opp-text) !important;
            }

            .opp-header {
                background: var(--opp-surface);
                border: 1px solid var(--opp-border);
                border-radius: 18px;
                padding: 1.25rem 1.35rem;
                margin-bottom: 1.1rem;
                backdrop-filter: blur(8px);
                box-shadow: 0 10px 36px rgba(3, 9, 22, 0.35);
            }

            .opp-header--wide {
                width: calc(100% + 1.75rem);
                margin-left: -0.875rem;
            }

            .opp-header-main {
                display: flex;
                align-items: center;
                gap: 0.9rem;
            }

            .opp-header-icon {
                width: 42px;
                height: 42px;
                flex-shrink: 0;
                opacity: 0.95;
            }

            .opp-header-kicker {
                text-transform: uppercase;
                letter-spacing: 0.12em;
                font-size: 0.73rem;
                font-weight: 700;
                color: #87aef2;
                margin-bottom: 0.35rem;
            }

            .opp-header-title {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.9rem;
                line-height: 1.2;
                color: var(--opp-text);
                margin: 0;
            }

            .opp-header-subtitle {
                margin-top: 0.4rem;
                font-size: 0.97rem;
                color: var(--opp-muted);
                margin-bottom: 0;
            }

            @media (max-width: 700px) {
                .opp-header--wide {
                    width: calc(100% + 0.75rem);
                    margin-left: -0.375rem;
                }

                .opp-header-main {
                    align-items: flex-start;
                }

                .opp-header-icon {
                    width: 34px;
                    height: 34px;
                }

                .opp-header-title {
                    font-size: 1.45rem;
                }
            }

            .opp-footer-note {
                margin-top: 1rem;
                text-align: center;
                font-size: 0.82rem;
                color: #95abd2;
            }

            div[data-testid='stButton'] > button,
            div[data-testid='baseButton-secondary'] > button,
            div[data-testid='baseButton-tertiary'] > button {
                border-radius: 12px;
            }

            .stTextInput > div > div,
            .stTextArea textarea,
            .stSelectbox > div > div,
            .stNumberInput > div > div {
                border-radius: 12px;
                background: rgba(10, 24, 47, 0.82);
                border: 1px solid var(--opp-border);
                color: var(--opp-text);
            }

            div[data-baseweb='select'] > div,
            .stTextArea textarea,
            input, textarea {
                color: var(--opp-text) !important;
            }

            .stAlert {
                background: rgba(14, 29, 56, 0.8);
                border: 1px solid var(--opp-border);
            }

            hr {
                border-color: var(--opp-border);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )