import streamlit as st


def restore_session() -> None:
    """Re-hydrate session_state.user from the ?u= URL param after a page reload."""
    if st.session_state.get("user"):
        return
    email = st.query_params.get("u")
    if not email:
        return
    from db import get_user_by_email  # local import to avoid top-level circular dep
    user = get_user_by_email(email)
    if user:
        st.session_state.user = user


def inject_fonts() -> None:
    """Inject Anton (headings/buttons) + Roboto (body) across every page."""
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Anton&family=Roboto:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            /* ── Headings ─────────────────────────────────────────────────── */
            h1, h2, h3, h4 {
                font-family: 'Anton', sans-serif !important;
                letter-spacing: 0px !important;
            }

            /* ── Body / markdown / captions ──────────────────────────────── */
            p, li,
            div[data-testid="stMarkdownContainer"],
            div[data-testid="stMarkdownContainer"] span,
            div[data-testid="stCaptionContainer"] {
                font-family: 'Roboto', sans-serif !important;
            }

            /* ── Widget labels ────────────────────────────────────────────── */
            label, .stSelectbox label, .stTextInput label,
            .stNumberInput label, .stRadio label {
                font-family: 'Roboto', sans-serif !important;
                font-weight: 500 !important;
            }

            /* ── Buttons ──────────────────────────────────────────────────── */
            .stButton button, .stFormSubmitButton button {
                font-family: 'Anton', sans-serif !important;
                letter-spacing: 1.2px !important;
            }

            /* ── Sidebar ──────────────────────────────────────────────────── */
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] a,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebarNavItems"] {
                font-family: 'Roboto', sans-serif !important;
            }

            /* ── Metric labels ────────────────────────────────────────────── */
            [data-testid="stMetricLabel"] > div {
                font-family: 'Roboto', sans-serif !important;
                font-weight: 600 !important;
            }

            /* ── Tab labels ───────────────────────────────────────────────── */
            button[data-baseweb="tab"] {
                font-family: 'Anton', sans-serif !important;
                letter-spacing: 1px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
