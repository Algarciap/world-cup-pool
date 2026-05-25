import streamlit as st
from db import get_or_create_user, is_locked

st.set_page_config(
    page_title="Mundial 2026 Pool",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Maintenance mode ───────────────────────────────────────────────────────────
MAINTENANCE = True
if MAINTENANCE:
    st.title("⚽ World Cup 2026 — Prediction Pool")
    st.info("🔧 We're making some improvements. Check back soon!")
    st.stop()
# ──────────────────────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    st.session_state.user = None

st.title("⚽ World Cup 2026 — Prediction Pool")

# ── Login ──────────────────────────────────────────────────────────────────────
if st.session_state.user is None:
    st.markdown(
        "Enter your **name** and **email** to join the pool. "
        "If you already registered, use the same email to recover your predictions."
    )
    with st.form("login"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Enter ▶")

    if submitted:
        name = name.strip()
        email = email.strip().lower()
        if not name or not email:
            st.error("Please fill in your name and email.")
        elif "@" not in email or "." not in email.split("@")[-1]:
            st.error("That email doesn't look valid.")
        else:
            with st.spinner("Looking up your account…"):
                user = get_or_create_user(name, email)
            st.session_state.user = user
            st.rerun()

# ── Logged-in home ─────────────────────────────────────────────────────────────
else:
    user = st.session_state.user
    st.success(f"👋 Welcome, **{user['name']}**!")

    if is_locked():
        st.warning(
            "🔒 Predictions are **locked**. The tournament has started. "
            "You can still check the leaderboard."
        )
    else:
        st.info(
            "✅ Predictions are open until **June 11, 2026 at 19:00 UTC** (tournament kick-off)."
        )

    st.markdown("---")
    st.markdown("### Navigate to:")

    c1, c2, c3 = st.columns(3)
    c1.page_link("pages/1_Predictions.py", label="⚽ My Predictions")
    c2.page_link("pages/2_Leaderboard.py", label="📊 Leaderboard")
    c3.page_link("pages/3_Admin.py",        label="🔧 Admin panel")

    st.markdown("---")
    st.markdown("### 🏆 Scoring system")
    st.markdown(
        """
| Category | Points |
|---|---|
| ✅ Correct match result (win/draw) | **3 pts** |
| 🎯 Exact scoreline bonus | **+2 pts** |
| 🥇 Correct group 1st place | **+4 pts** |
| 🥈 Correct group 2nd place | **+3 pts** |
| 🥉 Correct group 3rd place | **+2 pts** |
| Round of 32 — correct winner | **2 pts** |
| Round of 16 — correct winner | **4 pts** |
| Quarter-Finals — correct winner | **6 pts** |
| Semi-Finals — correct winner | **8 pts** |
| 3rd place match — correct winner | **5 pts** |
| 🏆 Final — correct winner | **15 pts** |
"""
    )

    st.markdown("---")
    if st.button("Log out"):
        st.session_state.clear()
        st.rerun()
