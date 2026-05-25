import os
import streamlit as st
from db import get_all_matches, update_match_result, calculate_group_points, calculate_knockout_points, flag_img

st.set_page_config(page_title="Admin — World Cup 2026", page_icon="🔧", layout="wide")

st.title("🔧 Admin Panel")

# ── Password gate ──────────────────────────────────────────────────────────────
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "") or os.getenv("ADMIN_PASSWORD", "")

if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

if not st.session_state.admin_ok:
    with st.form("admin_login"):
        pwd = st.text_input("Admin password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if ADMIN_PASSWORD and pwd == ADMIN_PASSWORD:
            st.session_state.admin_ok = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

st.success("✅ Admin session active.")

# ── Match data ─────────────────────────────────────────────────────────────────
all_matches = get_all_matches()
upcoming = [m for m in all_matches if m["status"] == "upcoming"]
finished  = [m for m in all_matches if m["status"] == "finished"]

# ── Enter results ──────────────────────────────────────────────────────────────
st.subheader(f"Upcoming matches ({len(upcoming)})")

if not upcoming:
    st.info("No pending matches.")
else:
    for match in upcoming:
        label = (
            f"{flag_img(match['home_team'])}{match['home_team']} "
            f"vs {flag_img(match['away_team'])}{match['away_team']} "
            f"— {match['match_date'][:10]}"
        )
        with st.expander(label, expanded=False):
            with st.form(f"result_{match['id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    hs = st.number_input(
                        f"Goals — {match['home_team']}",
                        min_value=0, max_value=20, step=1,
                        key=f"hs_{match['id']}",
                    )
                with col2:
                    as_ = st.number_input(
                        f"Goals — {match['away_team']}",
                        min_value=0, max_value=20, step=1,
                        key=f"as_{match['id']}",
                    )
                save = st.form_submit_button("💾 Save result")

            if save:
                update_match_result(match["id"], int(hs), int(as_))
                # Group stage: check if all 6 group matches are done → award group pts
                if match.get("group_name"):
                    calculate_group_points(match["group_name"])
                # Knockout stage: award knockout prediction pts
                if match.get("slot"):
                    winner = match["home_team"] if hs > as_ else match["away_team"]
                    calculate_knockout_points(match["slot"], winner)
                st.success(
                    f"✅ Result saved: {match['home_team']} {int(hs)} – {int(as_)} {match['away_team']}"
                )
                st.rerun()

# ── Finished results ───────────────────────────────────────────────────────────
st.subheader(f"Finished matches ({len(finished)})")
for match in finished:
    st.markdown(
        f"✅ {flag_img(match['home_team'])}{match['home_team']} **{match['home_score']}** – "
        f"**{match['away_score']}** {flag_img(match['away_team'])}{match['away_team']}  "
        f"({match['match_date'][:10]})",
        unsafe_allow_html=True,
    )

st.markdown("---")
if st.button("Sign out of admin"):
    st.session_state.admin_ok = False
    st.rerun()
