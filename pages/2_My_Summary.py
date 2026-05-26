import streamlit as st
from ui import inject_fonts, restore_session
from db import get_user_group_preds, get_user_knockout_preds, get_teams_by_group, flag_img, with_flag

st.set_page_config(page_title="My Summary — World Cup 2026", page_icon="📋", layout="wide")
inject_fonts()
restore_session()

# ── Auth guard ─────────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("⚠️ You need to log in first.")
    st.page_link("app.py", label="← Back to home")
    st.stop()

user = st.session_state.user

st.title("📋 My Prediction Slip")
st.caption("A read-only overview of everything you've predicted.")

# ── Load data ──────────────────────────────────────────────────────────────────
group_preds  = get_user_group_preds(user["id"])
ko_preds     = get_user_knockout_preds(user["id"])
teams_by_grp = get_teams_by_group()

# ── Progress metrics ───────────────────────────────────────────────────────────
champion = ko_preds.get("FINAL", {}).get("predicted_winner")

mc1, mc2, mc3 = st.columns(3)
with mc1:
    grp_delta = "✅ Complete!" if len(group_preds) == 12 else f"{12 - len(group_preds)} group(s) remaining"
    st.metric("⚽ Groups completed", f"{len(group_preds)} / 12", grp_delta)
with mc2:
    st.metric("🎯 Knockout picks", f"{len(ko_preds)} / 32")
with mc3:
    st.metric("🏆 Predicted champion", champion or "— not yet picked")

if not group_preds:
    st.divider()
    st.info("You haven't submitted any predictions yet.")
    st.page_link("pages/1_Predictions.py", label="⚽ Go to Predictions →")
    st.stop()

st.divider()

# ── Champion highlight ─────────────────────────────────────────────────────────
if champion:
    st.markdown(
        f"""<div style="background:linear-gradient(90deg,#1a3d1a,#2d7d2d);border-radius:10px;
            padding:16px 24px;display:flex;align-items:center;gap:20px;margin-bottom:12px">
          <span style="font-size:2.5rem">🏆</span>
          <div>
            <div style="color:#aaa;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px">
                Your predicted champion
            </div>
            <div style="font-size:1.6rem;font-weight:bold;color:#FFD700">
                {flag_img(champion)}&nbsp;{champion}
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Group stage predictions ────────────────────────────────────────────────────
st.subheader("⚽ Group Stage")

MEDALS = ["🥇", "🥈", "🥉"]
COLS_PER_ROW = 4
group_list = sorted(group_preds.keys())

for row_start in range(0, len(group_list), COLS_PER_ROW):
    row_groups = group_list[row_start : row_start + COLS_PER_ROW]
    cols = st.columns(COLS_PER_ROW)
    for i, col in enumerate(cols):
        if i >= len(row_groups):
            break
        g    = row_groups[i]
        pred = group_preds[g]
        with col:
            st.markdown(f"**Group {g}**")
            for medal, place_key in zip(MEDALS, ["first_place", "second_place", "third_place"]):
                team = pred.get(place_key)
                if team:
                    st.markdown(f"{medal} {flag_img(team)}{team}", unsafe_allow_html=True)
            st.markdown("")

# ── Knockout predictions ───────────────────────────────────────────────────────
if ko_preds:
    st.divider()
    st.subheader("🎯 Knockout Stage")

    ROUND_SLOTS = [
        ("Round of 32",    [f"R32_{i}" for i in range(1, 17)]),
        ("Round of 16",    [f"R16_{i}" for i in range(1, 9)]),
        ("Quarter-Finals", [f"QF_{i}"  for i in range(1, 5)]),
        ("Semi-Finals",    ["SF_1", "SF_2"]),
        ("3rd Place Match",["THIRD_PLACE"]),
        ("Final 🏆",       ["FINAL"]),
    ]

    for round_name, slots in ROUND_SLOTS:
        picks = {s: ko_preds[s]["predicted_winner"] for s in slots if s in ko_preds}
        if not picks:
            continue
        st.markdown(f"**{round_name}**")
        n_cols = min(len(picks), 4)
        cols   = st.columns(n_cols)
        for i, (_, team) in enumerate(picks.items()):
            with cols[i % n_cols]:
                st.markdown(f"{flag_img(team)}<b>{team}</b>", unsafe_allow_html=True)
        st.markdown("")

# ── Share your picks ──────────────────────────────────────────────────────────────────────────────
st.divider()
with st.expander("📤 Share your picks", expanded=False):
    lines = ["🏆 My World Cup 2026 Picks\n"]
    if champion:
        lines.append(f"Champion: {with_flag(champion)}")
    if group_preds:
        lines.append("\n⚽ Group Stage:")
        for g in sorted(group_preds.keys()):
            pred = group_preds[g]
            p1   = pred.get("first_place",  "")
            p2   = pred.get("second_place", "")
            p3   = pred.get("third_place",  "")
            lines.append(
                f"  Group {g}:  🥇{with_flag(p1)}  🥈{with_flag(p2)}  🥉{with_flag(p3)}"
            )
    share_text = "\n".join(lines)
    st.code(share_text, language=None)
    st.caption("Copy the text above and drop it in your group chat 🎉")

st.divider()
st.page_link("pages/1_Predictions.py", label="✏️ Edit my predictions →")
