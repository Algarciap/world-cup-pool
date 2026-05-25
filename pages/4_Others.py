import streamlit as st
from db import get_all_users_predictions, is_locked, flag_img

st.set_page_config(
    page_title="Others' Predictions — World Cup 2026", page_icon="👥", layout="wide"
)

# ── Auth guard ─────────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("⚠️ You need to log in first.")
    st.page_link("app.py", label="← Back to home")
    st.stop()

st.title("👥 Others' Predictions")

if not is_locked():
    st.info("🔒 Others' predictions will be visible once the tournament kicks off (June 11, 2026 at 19:00 UTC).")
    st.stop()

# ── Load all predictions ───────────────────────────────────────────────────────
data = get_all_users_predictions()
users = data["users"]
by_user_group = data["group_preds"]
by_user_ko = data["ko_preds"]

if not users:
    st.info("No predictions submitted yet.")
    st.stop()

# ── User picker ────────────────────────────────────────────────────────────────
user_names = [u["name"] for u in users]
selected_name = st.selectbox("Select a participant", user_names)
selected_user = next((u for u in users if u["name"] == selected_name), None)

if not selected_user:
    st.stop()

uid = selected_user["id"]
user_group_preds = by_user_group.get(uid, {})
user_ko_preds = by_user_ko.get(uid, {})

if not user_group_preds:
    st.info(f"{selected_name} hasn't submitted any predictions yet.")
    st.stop()

# ── Group predictions ──────────────────────────────────────────────────────────
st.subheader("Group Stage Predictions")

group_names = sorted(user_group_preds.keys())
cols_per_row = 4
for row_start in range(0, len(group_names), cols_per_row):
    row_groups = group_names[row_start : row_start + cols_per_row]
    cols = st.columns(len(row_groups))
    for col, group in zip(cols, row_groups):
        pred = user_group_preds[group]
        with col:
            st.markdown(f"**Group {group}**")
            medals = ["🥇", "🥈", "🥉"]
            places = [pred.get("first_place"), pred.get("second_place"), pred.get("third_place")]
            for medal, team in zip(medals, places):
                if team:
                    st.markdown(
                        f"{medal} {flag_img(team)}{team}",
                        unsafe_allow_html=True,
                    )

# ── Knockout predictions ───────────────────────────────────────────────────────
if user_ko_preds:
    st.divider()
    st.subheader("Knockout Predictions")

    ROUND_SLOTS = [
        ("Round of 32", [f"R32_{i}" for i in range(1, 17)]),
        ("Round of 16", [f"R16_{i}" for i in range(1, 9)]),
        ("Quarter-Finals", [f"QF_{i}" for i in range(1, 5)]),
        ("Semi-Finals", ["SF_1", "SF_2"]),
        ("3rd Place Match", ["THIRD_PLACE"]),
        ("Final 🏆", ["FINAL"]),
    ]

    for round_name, slots in ROUND_SLOTS:
        picks = {s: user_ko_preds[s]["predicted_winner"] for s in slots if s in user_ko_preds}
        if not picks:
            continue
        st.markdown(f"**{round_name}**")
        n_cols = min(len(picks), 4)
        cols = st.columns(n_cols)
        for i, (slot, team) in enumerate(picks.items()):
            with cols[i % n_cols]:
                st.markdown(
                    f"{flag_img(team)}<b>{team}</b>",
                    unsafe_allow_html=True,
                )
