import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from ui import inject_fonts, restore_session
from db import get_leaderboard, get_all_users_predictions, is_locked, flag_img

st.set_page_config(page_title="Leaderboard — World Cup 2026", page_icon="📊", layout="wide")
inject_fonts()
restore_session()

st.title("📊 Leaderboard")
_now = datetime.now(timezone.utc).strftime("%b %d, %H:%M UTC")
st.markdown(
    f"Total points accumulated by each participant.   "
    f"<span style='color:#888;font-size:0.8rem'>Last calculated: {_now}</span>",
    unsafe_allow_html=True,
)

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

    # ── Rank-movement snapshot ───────────────────────────────────────────────────
    if "_lb_snapshot" not in st.session_state:
        st.session_state["_lb_snapshot"] = {r["name"]: i + 1 for i, r in enumerate(leaderboard)}
    prev_ranks = st.session_state["_lb_snapshot"]

    # Keep only the columns we want to display, in order
    display_cols = [c for c in ["Name", "Total", "Matches", "Group bonus", "Knockout"] if c in df.columns]
    df = df[display_cols].sort_values("Total", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Pos."

    def _rank_delta(name: str, pos: int) -> str:
        prev = prev_ranks.get(name)
        if prev is None:
            return "🆕"
        d = prev - pos
        if d > 0:
            return f"▲{d}"
        if d < 0:
            return f"▼{abs(d)}"
        return "—"

    df.insert(1, "Δ", [_rank_delta(row["Name"], idx) for idx, row in df.iterrows()])

    current_user = st.session_state.get("user")
    current_user_name = current_user["name"] if current_user else None

    def _highlight_me(row):
        if current_user_name and row["Name"] == current_user_name:
            return ["background-color: rgba(255, 215, 0, 0.3); font-weight: bold"] * len(row)
        return [""] * len(row)

    st.caption("Δ = rank change since your last refresh · Your row is highlighted in gold")
    st.dataframe(df.style.apply(_highlight_me, axis=1), use_container_width=True)

    # ── Visual podium ───────────────────────────────────────────────────────────
    st.markdown("---")
    rows = leaderboard  # already sorted DESC by the view

    def _podium_slot(row, medal, bg, height_px, name_color, rank_label):
        if row is None:
            return "<div style='width:33%'></div>"
        name = row.get("name", "?")
        pts  = row.get("total_points", 0)
        return (
            f"<div style='text-align:center;width:33%;'>"
            f"<div style='font-size:2rem'>{medal}</div>"
            f"<div style='font-weight:bold;color:{name_color};font-size:0.95rem;"
            f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:0 4px'>{name}</div>"
            f"<div style='color:#aaaaaa;font-size:0.8rem;margin-bottom:6px'>{pts} pts</div>"
            f"<div style='background:{bg};height:{height_px}px;border-radius:6px 6px 0 0;"
            f"display:flex;align-items:center;justify-content:center;'>"
            f"<span style='color:rgba(255,255,255,0.5);font-size:1.6rem;font-weight:bold'>{rank_label}</span>"
            f"</div></div>"
        )

    p1 = rows[0] if len(rows) >= 1 else None
    p2 = rows[1] if len(rows) >= 2 else None
    p3 = rows[2] if len(rows) >= 3 else None

    podium_html = (
        "<div style='display:flex;align-items:flex-end;justify-content:center;"
        "gap:8px;padding:16px 0;font-family:sans-serif;max-width:560px;margin:0 auto'>"
        + _podium_slot(p2, "🥈", "linear-gradient(180deg,#9e9e9e,#616161)", 90,  "#e0e0e0", "2")
        + _podium_slot(p1, "🥇", "linear-gradient(180deg,#FFD700,#F59E0B)", 130, "#FFD700", "1")
        + _podium_slot(p3, "🥉", "linear-gradient(180deg,#cd7f32,#8B4513)",  60,  "#d4956a", "3")
        + "</div>"
    )
    st.markdown(podium_html, unsafe_allow_html=True)

if st.button("🔄 Refresh"):
    if leaderboard:
        st.session_state["_lb_snapshot"] = {r["name"]: i + 1 for i, r in enumerate(leaderboard)}
    st.rerun()

# ── Champion picks tally ──────────────────────────────────────────────────────────────────────
if is_locked():
    from collections import Counter
    all_data    = get_all_users_predictions()
    champ_picks = [
        ud.get("FINAL", {}).get("predicted_winner")
        for ud in all_data["ko_preds"].values()
    ]
    champ_picks = [c for c in champ_picks if c]
    if champ_picks:
        counts = Counter(champ_picks)
        st.markdown("---")
        st.subheader("🏆 Champion Picks")
        st.caption("Who each participant is backing to lift the trophy")
        total_picks = len(champ_picks)
        for team, n in counts.most_common():
            bar_w = max(6, int((n / total_picks) * 240))
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:12px;margin:5px 0'>"
                f"<div style='width:160px;text-align:right;font-size:0.9rem'>"
                f"{flag_img(team)}&nbsp;{team}</div>"
                f"<div style='background:#E8002A;height:18px;border-radius:4px;"
                f"width:{bar_w}px;flex-shrink:0'></div>"
                f"<div style='color:#aaa;font-size:0.85rem'>"
                f"{n} pick{'s' if n != 1 else ''}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
