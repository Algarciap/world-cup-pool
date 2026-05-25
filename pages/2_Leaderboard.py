import streamlit as st
import pandas as pd
from db import get_leaderboard

st.set_page_config(page_title="Leaderboard — World Cup 2026", page_icon="📊", layout="wide")

st.title("📊 Leaderboard")
st.markdown("Total points accumulated by each participant.")

leaderboard = get_leaderboard()

if not leaderboard:
    st.info("No scores yet — the tournament hasn't started!")
else:
    df = pd.DataFrame(leaderboard)
    df = df.rename(columns={
        "name":                    "Name",
        "total_points":            "Total",
        "group_stage_points":      "Matches",
        "group_prediction_points": "Group bonus",
        "knockout_points":         "Knockout",
    })

    # Keep only the columns we want to display, in order
    display_cols = [c for c in ["Name", "Total", "Matches", "Groups", "Knockout"] if c in df.columns]
    df = df[display_cols].sort_values("Total", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Pos."

    st.dataframe(df, use_container_width=True)

    # Top 3 podium
    st.markdown("---")
    rows = leaderboard  # already sorted DESC by the view
    if len(rows) >= 1:
        st.markdown(f"🥇 **{rows[0].get('name', '?')}** — {rows[0].get('total_points', 0)} pts")
    if len(rows) >= 2:
        st.markdown(f"🥈 **{rows[1].get('name', '?')}** — {rows[1].get('total_points', 0)} pts")
    if len(rows) >= 3:
        st.markdown(f"🥉 **{rows[2].get('name', '?')}** — {rows[2].get('total_points', 0)} pts")

if st.button("🔄 Refresh"):
    st.rerun()
