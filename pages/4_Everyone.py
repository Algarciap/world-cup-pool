import streamlit as st
from ui import inject_fonts, restore_session
from db import get_all_users_predictions, get_completion_stats, is_locked, flag_img

st.set_page_config(
    page_title="Everyone's Picks — World Cup 2026", page_icon="👥", layout="wide"
)
inject_fonts()
restore_session()

# ── Auth guard ─────────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("⚠️ You need to log in first.")
    st.page_link("app.py", label="← Back to home")
    st.stop()

st.title("👥 Everyone's Picks")

if not is_locked():
    stats = get_completion_stats()
    done, total = stats.get("completed", 0), stats.get("total", 0)
    if done > 0:
        st.info(
            f"🔒 **{done} out of {total} participants** have submitted their full predictions. "
            "Come back on **June 11 at 19:00 UTC** to see who they picked!"
        )
    else:
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

# ── Participant card grid ──────────────────────────────────────────────────────
if "selected_participant_id" not in st.session_state:
    st.session_state.selected_participant_id = None

CARDS_PER_ROW = 4
for row_start in range(0, len(users), CARDS_PER_ROW):
    row_users = users[row_start : row_start + CARDS_PER_ROW]
    cols = st.columns(CARDS_PER_ROW)
    for i, col in enumerate(cols):
        if i >= len(row_users):
            break
        u = row_users[i]
        uid = u["id"]
        champion = by_user_ko.get(uid, {}).get("FINAL", {}).get("predicted_winner")
        champ_display = (
            f"{flag_img(champion)}&nbsp;{champion}" if champion else "— not picked"
        )
        is_selected = st.session_state.selected_participant_id == uid
        border = "#FFD700" if is_selected else "rgba(255,255,255,0.15)"
        with col:
            st.markdown(
                f"""<div style="border:2px solid {border};border-radius:10px;
                    padding:14px 10px;text-align:center;
                    background:rgba(255,255,255,0.04);margin-bottom:4px">
                  <div style="font-size:1.1rem;color:#ffffff;margin-bottom:6px">{u['name']}</div>
                  <div style="font-size:0.75rem;color:#888;text-transform:uppercase;
                      letter-spacing:0.5px;margin-bottom:4px">🏆 Champion pick</div>
                  <div style="font-size:0.95rem;color:#FFD700">{champ_display}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            btn_label = "✓ Selected" if is_selected else "View"
            if st.button(
                btn_label, key=f"card_{uid}", use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state.selected_participant_id = uid
                st.rerun()

# ── Selected user's predictions ────────────────────────────────────────────────
selected_uid = st.session_state.selected_participant_id
if selected_uid is None:
    st.stop()

selected_user = next((u for u in users if u["id"] == selected_uid), None)
if not selected_user:
    st.stop()

selected_name = selected_user["name"]
user_group_preds = by_user_group.get(selected_uid, {})
user_ko_preds    = by_user_ko.get(selected_uid, {})

if not user_group_preds:
    st.info(f"{selected_name} hasn't submitted any predictions yet.")
    st.stop()

st.divider()
st.subheader(f"📋 {selected_name}'s Predictions")

# ── Group predictions ──────────────────────────────────────────────────────────
st.markdown("**Group Stage**")

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
    st.markdown("**Knockout Stage**")

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
