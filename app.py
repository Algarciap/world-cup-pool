import streamlit as st
import streamlit.components.v1 as components
from ui import inject_fonts, restore_session
from db import get_or_create_user, is_locked, get_completion_stats, get_user_group_preds, get_user_knockout_preds, flag_img, OFFICES, update_user_office

st.set_page_config(
    page_title="Mundial 2026 Pool",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_fonts()

# ── Maintenance mode ───────────────────────────────────────────────────────────
MAINTENANCE = True
if MAINTENANCE:
    st.title("⚽ World Cup 2026 — Prediction Pool")
    st.info("🔧 We're making some improvements. Check back soon!")
    st.stop()
# ──────────────────────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    st.session_state.user = None
restore_session()

st.title("⚽ World Cup 2026 — Prediction Pool")

# ── Login ──────────────────────────────────────────────────────────────────────
if st.session_state.user is None:
    st.markdown(
        "Enter your **name** and **email** to join the pool. "
        "If you already registered, use the same email to recover your predictions."
    )
    st.caption("🔓 No password needed — this is a friendly pool, not a bank.")
    with st.form("login"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        office = st.selectbox(
            "Which office are you in?",
            options=OFFICES,
            help="Returning? Your office is already saved — this is only used on first sign-up.",
        )
        submitted = st.form_submit_button("Enter ▶")

    if submitted:
        name = name.strip()
        email = email.strip().lower()
        if not name or not email:
            st.error("Please fill in your name and email.")
        elif "@" not in email or "." not in email.split("@")[-1]:
            st.error("That email doesn't look valid.")
        elif not email.endswith("@kingmakers.com"):
            st.error("This pool is only open to Kingmakers staff. Please use your @kingmakers.com email.")
        else:
            with st.spinner("Looking up your account…"):
                user = get_or_create_user(name, email, office)
            st.session_state.user = user
            st.query_params["u"] = user["email"]
            st.rerun()

# ── Logged-in home ─────────────────────────────────────────────────────────────
else:
    user = st.session_state.user
    st.success(f"👋 Welcome, **{user['name']}**!")

    # ── Office picker for existing users who haven't set one yet ──────────────
    if not user.get("office"):
        st.info(
            "👋 One last thing — we've added **office leaderboards**. "
            "Please tell us which office you're in so we can include you."
        )
        with st.form("office_update"):
            picked_office = st.selectbox("Your office", OFFICES)
            if st.form_submit_button("Save & continue →"):
                update_user_office(user["id"], picked_office)
                st.session_state.user = {**user, "office": picked_office}
                st.rerun()
        st.stop()
    # ─────────────────────────────────────────────────────────────────────────

    stats = get_completion_stats()
    done, total = stats["completed"], stats["total"]
    if total > 0:
        if done == total:
            st.caption(f"✅ All {total} participants have submitted their full predictions — you're set!")
        else:
            st.caption(f"📊 {done}/{total} participants have completed their predictions. Don't be left behind!")

    if is_locked():
        st.warning(
            "🔒 Predictions are **locked**. The tournament has started. "
            "You can still check the leaderboard."
        )
    else:
        components.html(
            """
            <link href="https://fonts.googleapis.com/css2?family=Anton&display=swap" rel="stylesheet">
            <div style="background: linear-gradient(90deg, #003087 0%, #00843d 100%); border-radius: 8px; padding: 14px 20px; display: flex; flex-wrap: wrap; align-items: center; gap: 16px; color: white; font-family: 'Anton', sans-serif;">
              <span style="font-size: 1em; opacity: 0.9;">⏳ PREDICTIONS CLOSE IN:</span>
              <span id="cd" style="font-size: 1.5em; letter-spacing: 0px; font-variant-numeric: tabular-nums;">calculating…</span>
            </div>
            <script>
              (function() {
                var target = new Date('2026-06-11T19:00:00Z').getTime();
                function update() {
                  var now = Date.now();
                  var diff = target - now;
                  if (diff <= 0) {
                    document.getElementById('cd').textContent = '🔒 Locked';
                    return;
                  }
                  var d = Math.floor(diff / 86400000);
                  var h = Math.floor((diff % 86400000) / 3600000);
                  var m = Math.floor((diff % 3600000) / 60000);
                  var s = Math.floor((diff % 60000) / 1000);
                  document.getElementById('cd').textContent =
                    d + 'd ' + String(h).padStart(2, '0') + 'h ' + String(m).padStart(2, '0') + 'm ' + String(s).padStart(2, '0') + 's';
                }
                update();
                setInterval(update, 1000);
              })();
            </script>
            """,
            height=70,
        )

    # ── Personal champion card + context CTA ──────────────────────────────────
    user_ko  = get_user_knockout_preds(user["id"])
    user_grp = get_user_group_preds(user["id"])
    champion = user_ko.get("FINAL", {}).get("predicted_winner")
    n_done   = len(user_grp)

    st.markdown("---")
    if champion:
        _fi = flag_img(champion, 28)
        st.markdown(
            f"""<div style="background:linear-gradient(90deg,#1a3d1a,#2d7d2d);
                border-radius:10px;padding:12px 20px;display:flex;align-items:center;
                gap:16px;margin-bottom:12px">
              <span style="font-size:2rem">🏆</span>
              <div>
                <div style="color:#aaa;font-size:0.7rem;text-transform:uppercase;letter-spacing:2px">Your champion pick</div>
                <div style="font-size:1.3rem;font-weight:bold;color:#FFD700">{_fi}&nbsp;{champion}</div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    if not is_locked():
        if n_done == 12 and champion:
            st.success("🎉 **You're all set!** Come back June 11 to see everyone's picks.")
        elif n_done == 12:
            st.info("🎯 Groups done! Complete your **knockout bracket** to finish your entry.")
            st.page_link("pages/1_Predictions.py", label="🏆 Open Knockout tab →")
        elif n_done > 0:
            st.info(f"⚽ **{12 - n_done} group(s) remaining** — don't stop now!")
            st.page_link("pages/1_Predictions.py", label="⚽ Continue predictions →")
        else:
            st.info("👋 Pick your match scores to enter the pool!")
            st.page_link("pages/1_Predictions.py", label="⚽ Start predicting →")

    c1, c2, c3 = st.columns(3)
    c1.page_link("pages/1_Predictions.py", label="⚽ My Predictions")
    c2.page_link("pages/2_My_Summary.py",  label="📋 My Summary")
    c3.page_link("pages/3_Leaderboard.py", label="📊 Leaderboard")

    st.markdown("---")
    with st.expander("🏆 Scoring system", expanded=False):
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
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()
