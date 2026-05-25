import streamlit as st
from db import (
    get_teams_by_group,
    get_group_matches,
    get_user_bets,
    upsert_bet,
    derive_and_save_group_prediction,
    get_user_group_preds,
    get_user_knockout_preds,
    upsert_knockout_pred,
    is_locked,
    flag_img,
)

st.set_page_config(
    page_title="Predictions — World Cup 2026", page_icon="⚽", layout="wide"
)

# ── Auth guard ─────────────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("⚠️ You need to log in first.")
    st.page_link("app.py", label="← Back to home")
    st.stop()

user = st.session_state.user
locked = is_locked()

st.title("⚽ My Predictions")
if locked:
    st.warning("🔒 Predictions are locked. The tournament has started.")

with st.expander("🏆 Scoring system", expanded=False):
    st.markdown("""
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
""")

# ── Load data ──────────────────────────────────────────────────────────────────
# Pre-clear caches if a save just happened so tab icons are fresh on this render
if st.session_state.pop("_needs_fresh_data", False):
    get_user_bets.clear()
    get_user_group_preds.clear()
    get_user_knockout_preds.clear()

teams_by_group = get_teams_by_group()
matches_by_group = get_group_matches()
saved_bets = get_user_bets(user["id"])
saved_group_preds = get_user_group_preds(user["id"])
saved_ko_preds = get_user_knockout_preds(user["id"])
group_names = sorted(matches_by_group.keys())


def _compute_standings(
    batch: dict[int, tuple[str, int, int]], matches: list[dict]
) -> list[dict]:
    """Derive group standings from batch {match_id: (winner, home_score, away_score)}."""
    data: dict[str, dict] = {}
    for m in matches:
        h, a = m["home_team"], m["away_team"]
        for t in (h, a):
            data.setdefault(t, {"pts": 0, "gf": 0, "ga": 0})
        entry = batch.get(m["id"])
        if not entry:
            continue
        w, hs, as_ = entry
        data[h]["gf"] += hs
        data[h]["ga"] += as_
        data[a]["gf"] += as_
        data[a]["ga"] += hs
        if w == "home":
            data[h]["pts"] += 3
        elif w == "away":
            data[a]["pts"] += 3
        else:
            data[h]["pts"] += 1
            data[a]["pts"] += 1
    return sorted(
        [{"team": t, "pts": d["pts"], "gd": d["gf"] - d["ga"], "gf": d["gf"]}
         for t, d in data.items()],
        key=lambda x: (x["pts"], x["gd"], x["gf"]),
        reverse=True,
    )


def _show_standings(standings: list[dict]) -> None:
    MEDALS = ["🥇", "🥈", "🥉", "4️⃣"]
    rows = ""
    for i, s in enumerate(standings):
        medal = MEDALS[i] if i < len(MEDALS) else str(i + 1)
        gd_str = f"+{s['gd']}" if s["gd"] > 0 else str(s["gd"])
        rows += (
            f"<tr><td style='padding:3px 8px'>{medal}</td>"
            f"<td style='padding:3px 8px'>{flag_img(s['team'])}<b>{s['team']}</b></td>"
            f"<td style='padding:3px 8px; text-align:center'><b>{s['pts']}</b></td>"
            f"<td style='padding:3px 8px; text-align:center'>{gd_str}</td>"
            f"<td style='padding:3px 8px; text-align:center'>{s['gf']}</td></tr>\n"
        )
    table = (
        "<table style='border-collapse:collapse; margin:4px 0'>"
        "<thead><tr style='border-bottom:1px solid #555'>"
        "<th style='padding:3px 8px; text-align:left'>#</th>"
        "<th style='padding:3px 8px; text-align:left'>Team</th>"
        "<th style='padding:3px 8px'>Pts</th>"
        "<th style='padding:3px 8px'>GD</th>"
        "<th style='padding:3px 8px'>GF</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )
    st.markdown(table, unsafe_allow_html=True)



# ── Progress summary ──────────────────────────────────────────────────────────
done_groups = [g for g in group_names if g in saved_group_preds]
partial_groups = [
    g for g in group_names
    if g not in saved_group_preds
    and any(m["id"] in saved_bets for m in matches_by_group.get(g, []))
]
n_groups_done = len(done_groups)
n_ko_done = len(saved_ko_preds)
champion = saved_ko_preds.get("FINAL", {}).get("predicted_winner")

pc1, pc2, pc3 = st.columns(3)
with pc1:
    grp_delta = "\u2705 Complete!" if n_groups_done == 12 else f"{12 - n_groups_done} group(s) remaining"
    st.metric("\u26bd Group Predictions", f"{n_groups_done} / 12", grp_delta)
with pc2:
    st.metric("\U0001f3af Knockout Picks", f"{n_ko_done} / 31")
with pc3:
    st.metric("\U0001f3c6 Predicted Champion", champion or "\u2014 not yet picked")

st.divider()

# ── Two stable tabs ────────────────────────────────────────────────────────────
tab_groups, tab_ko = st.tabs(["\u26bd Group Predictions", "\U0001f3af Knockout"])

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# GROUP PREDICTIONS TAB
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
with tab_groups:
    if "active_group" not in st.session_state or st.session_state.active_group not in group_names:
        st.session_state.active_group = group_names[0]
    active_group = st.session_state.active_group
    group_idx = group_names.index(active_group)

    # ── Group selector buttons (A – L) ────────────────────────────────────────
    btn_cols = st.columns(len(group_names))
    for i, g in enumerate(group_names):
        with btn_cols[i]:
            if g in saved_group_preds:
                label = f"\u2705 {g}"
            elif g in partial_groups:
                label = f"\u26a0\ufe0f {g}"
            else:
                label = g
            if st.button(
                label, key=f"grp_btn_{g}",
                type="primary" if g == active_group else "secondary",
                use_container_width=True,
            ):
                st.session_state.active_group = g
                st.rerun()

    st.markdown("---")

    # ── Selected group content ─────────────────────────────────────────────────
    group = active_group
    matches = matches_by_group[group]
    teams = teams_by_group.get(group, [])

    teams_html = " \u00b7 ".join(f"{flag_img(t)}{t}" for t in teams)
    st.markdown(f"**Group {group}** &nbsp;&mdash;&nbsp; {teams_html}", unsafe_allow_html=True)

    if group in saved_group_preds:
        st.caption("\u2705 All 6 matches saved")
    elif any(m["id"] in saved_bets for m in matches):
        n_s = sum(1 for m in matches if m["id"] in saved_bets)
        st.caption(f"\u26a0\ufe0f {n_s}/{len(matches)} matches saved \u2014 remember to save all 6!")

    if st.session_state.get("_last_saved_group") == group:
        st.success(f"\u2705 Group {group} saved!")
        last_standings = st.session_state.get("_last_saved_standings")
        if last_standings:
            _show_standings(last_standings)
        st.session_state.pop("_last_saved_group", None)
        st.session_state.pop("_last_saved_standings", None)

    group_pred = saved_group_preds.get(group)

    # ── Match prediction form ──────────────────────────────────────────────────
    with st.form(f"form_{group}"):
        batch: dict[int, tuple[str, int, int]] = {}

        for match in matches:
            mid = match["id"]
            home = match["home_team"]
            away = match["away_team"]
            date_str = match["match_date"]
            existing = saved_bets.get(mid, {})

            # [flag + team name]  [home score]  [:]  [away score]  [team name + flag]
            c_home, c_hs, c_sep, c_as, c_away = st.columns([4, 1, 0.4, 1, 4])
            with c_home:
                st.markdown(
                    f'{flag_img(home, 24)}&nbsp;<span style="font-size:1rem;font-weight:600">{home}</span>',
                    unsafe_allow_html=True,
                )
            with c_hs:
                hs = st.number_input(
                    "Home", min_value=0, max_value=20,
                    value=existing.get("predicted_home_score") or 0,
                    step=1, disabled=locked, key=f"hs_{mid}",
                    label_visibility="collapsed",
                )
            with c_sep:
                st.markdown(
                    "<div style='text-align:center;padding-top:6px;font-size:1.4rem;font-weight:300'>:</div>",
                    unsafe_allow_html=True,
                )
            with c_as:
                as_ = st.number_input(
                    "Away", min_value=0, max_value=20,
                    value=existing.get("predicted_away_score") or 0,
                    step=1, disabled=locked, key=f"as_{mid}",
                    label_visibility="collapsed",
                )
            with c_away:
                st.markdown(
                    f'<div style="text-align:right"><span style="font-size:1rem;font-weight:600">'
                    f'{away}</span>&nbsp;{flag_img(away, 24)}</div>',
                    unsafe_allow_html=True,
                )

            if hs > as_:
                winner_code = "home"
                result_html = f'<span style="color:#4CAF50;font-size:0.85rem"><b>{home}</b> wins</span>'
            elif as_ > hs:
                winner_code = "away"
                result_html = f'<span style="color:#4CAF50;font-size:0.85rem"><b>{away}</b> wins</span>'
            else:
                winner_code = "draw"
                result_html = '<span style="color:#FFC107;font-size:0.85rem"><b>Draw</b></span>'

            st.markdown(
                f'<div style="text-align:center;margin:2px 0">{result_html}</div>'
                f'<div style="text-align:center;color:#888;font-size:0.75rem">'
                f'{date_str[:10]} {date_str[11:16]} UTC</div>',
                unsafe_allow_html=True,
            )
            st.divider()
            batch[mid] = (winner_code, int(hs), int(as_))

        submitted = st.form_submit_button(
            f"\U0001f4be Save Group {group}", disabled=locked, use_container_width=True,
        )

    if submitted and not locked:
        with st.spinner(f"Saving Group {group}..."):
            for mid, (w, hs_val, as_val) in batch.items():
                upsert_bet(user["id"], mid, w, hs_val, as_val)
            derive_and_save_group_prediction(user["id"], group)
        standings = _compute_standings(batch, matches)
        st.session_state._needs_fresh_data = True
        st.session_state._last_saved_group = group
        st.session_state._last_saved_standings = standings
        st.rerun()

    # ── Prev / Next navigation ─────────────────────────────────────────────────
    nav_l, _, nav_r = st.columns([2, 8, 2])
    with nav_l:
        if group_idx > 0:
            if st.button(f"\u2190 Group {group_names[group_idx - 1]}",
                         use_container_width=True):
                st.session_state.active_group = group_names[group_idx - 1]
                st.rerun()
    with nav_r:
        if group_idx < len(group_names) - 1:
            if st.button(f"Group {group_names[group_idx + 1]} \u2192",
                         use_container_width=True, type="primary"):
                st.session_state.active_group = group_names[group_idx + 1]
                st.rerun()
        else:
            st.caption("All groups done! Open the \U0001f3af Knockout tab.")

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# KNOCKOUT TAB
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
with tab_ko:
    all_done = len(done_groups) == len(group_names)
    if done_groups:
        with st.expander(
            f"\U0001f4ca Group Stage Summary ({len(done_groups)}/{len(group_names)} groups)",
            expanded=all_done,
        ):
            MEDALS = ["\U0001f947", "\U0001f948", "\U0001f949"]
            cols = st.columns(4)
            for i, g in enumerate(sorted(done_groups)):
                pred = saved_group_preds[g]
                with cols[i % 4]:
                    st.markdown(f"**Group {g}**")
                    for medal, place in zip(
                        MEDALS,
                        [pred.get("first_place"), pred.get("second_place"), pred.get("third_place")],
                    ):
                        if place:
                            st.markdown(
                                f"{medal} {flag_img(place)}{place}",
                                unsafe_allow_html=True,
                            )
                    st.markdown("")
        st.divider()

    if locked:
        st.warning("\U0001f512 Predictions are locked.")
    else:
        st.info(
            "Predict who wins each match. "
            "Once you save a round, the **next round shows who you predicted** "
            "to face each other \u2014 so the bracket builds itself."
        )

    all_teams = sorted(t for teams in teams_by_group.values() for t in teams)
    team_options = ["— Select team —"] + all_teams

    def _best_third(group_pool: list[str]) -> str | None:
        """Find the best predicted 3rd-place team from the given group pool
        based on the user's own predicted match scores."""
        candidates = []
        for g in group_pool:
            third = saved_group_preds.get(g, {}).get("third_place")
            if not third:
                continue
            pts, gd, gf = 0, 0, 0
            for m in matches_by_group.get(g, []):
                bet = saved_bets.get(m["id"], {})
                if not bet:
                    continue
                hs = bet.get("predicted_home_score") or 0
                as_ = bet.get("predicted_away_score") or 0
                if m["home_team"] == third:
                    gf += hs
                    gd += hs - as_
                    w = bet.get("predicted_winner")
                    if w == "home":
                        pts += 3
                    elif w == "draw":
                        pts += 1
                elif m["away_team"] == third:
                    gf += as_
                    gd += as_ - hs
                    w = bet.get("predicted_winner")
                    if w == "away":
                        pts += 3
                    elif w == "draw":
                        pts += 1
            candidates.append((third, pts, gd, gf))
        if not candidates:
            return None
        candidates.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
        return candidates[0][0]

    # Official FIFA 2026 R32 slot → group position sources
    R32_SOURCES: dict[str, tuple[str, str]] = {
        "R32_1":  ("1E",  "3ABCDF"),   # M74
        "R32_2":  ("1I",  "3CDFGH"),   # M77
        "R32_3":  ("2A",  "2B"),       # M73
        "R32_4":  ("1F",  "2C"),       # M75
        "R32_5":  ("1C",  "2F"),       # M76
        "R32_6":  ("2E",  "2I"),       # M78
        "R32_7":  ("1A",  "3CEFHI"),   # M79
        "R32_8":  ("1L",  "3EHIJK"),   # M80
        "R32_9":  ("2K",  "2L"),       # M83
        "R32_10": ("1H",  "2J"),       # M84
        "R32_11": ("1D",  "3BEFIJ"),   # M81
        "R32_12": ("1G",  "3AEHIJ"),   # M82
        "R32_13": ("1J",  "2H"),       # M86
        "R32_14": ("2D",  "2G"),       # M88
        "R32_15": ("1B",  "3EFGIJ"),   # M85
        "R32_16": ("1K",  "3DEIJL"),   # M87
    }

    # Which two slots feed into each higher-round slot (official bracket)
    BRACKET_FEEDERS: dict[str, tuple[str, str]] = {
        "R16_1": ("R32_1",  "R32_2"),   "R16_2": ("R32_3",  "R32_4"),
        "R16_3": ("R32_5",  "R32_6"),   "R16_4": ("R32_7",  "R32_8"),
        "R16_5": ("R32_9",  "R32_10"),  "R16_6": ("R32_11", "R32_12"),
        "R16_7": ("R32_13", "R32_14"),  "R16_8": ("R32_15", "R32_16"),
        # QF_2 feeds from R16_5+R16_6; QF_3 from R16_3+R16_4 (matches 97-100)
        "QF_1":  ("R16_1",  "R16_2"),   "QF_2":  ("R16_5",  "R16_6"),
        "QF_3":  ("R16_3",  "R16_4"),   "QF_4":  ("R16_7",  "R16_8"),
        "SF_1":  ("QF_1",   "QF_2"),    "SF_2":  ("QF_3",   "QF_4"),
        "FINAL": ("SF_1",   "SF_2"),
    }

    # Human-readable names for every slot
    SLOT_NAMES: dict[str, str] = {
        "R32_1":  "1E vs 3(A/B/C/D/F)",  "R32_2":  "1I vs 3(C/D/F/G/H)",
        "R32_3":  "2A vs 2B",            "R32_4":  "1F vs 2C",
        "R32_5":  "1C vs 2F",            "R32_6":  "2E vs 2I",
        "R32_7":  "1A vs 3(C/E/F/H/I)",  "R32_8":  "1L vs 3(E/H/I/J/K)",
        "R32_9":  "2K vs 2L",            "R32_10": "1H vs 2J",
        "R32_11": "1D vs 3(B/E/F/I/J)",  "R32_12": "1G vs 3(A/E/H/I/J)",
        "R32_13": "1J vs 2H",            "R32_14": "2D vs 2G",
        "R32_15": "1B vs 3(E/F/G/I/J)",  "R32_16": "1K vs 3(D/E/I/J/L)",
        **{f"R16_{i}": f"Round of 16 Match {i}" for i in range(1, 9)},
        **{f"QF_{i}":  f"Quarter-Final {i}"     for i in range(1, 5)},
        "SF_1": "Semi-Final 1", "SF_2": "Semi-Final 2",
        "FINAL": "Final", "THIRD_PLACE": "3rd Place Match",
    }

    def _resolve_pos(pos: str) -> str:
        """Convert '1E'/'2B'/'3ABCDF' to a team name or readable placeholder."""
        if len(pos) == 2 and pos[0] == "1":
            return saved_group_preds.get(pos[1], {}).get("first_place") or f"1st Group {pos[1]}"
        elif len(pos) == 2 and pos[0] == "2":
            return saved_group_preds.get(pos[1], {}).get("second_place") or f"2nd Group {pos[1]}"
        elif pos[0] == "3":
            group_pool = list(pos[1:])
            best = _best_third(group_pool)
            return best if best else f"Best 3rd ({'/' .join(group_pool)})"
        return pos

    def _team_idx(val: str | None, opts: list[str]) -> int:
        return opts.index(val) if val and val in opts else 0

    def _slot_teams(slot: str) -> tuple[str | None, str | None]:
        """Returns the two real team names for a slot if both are determinable, else (None, None)."""
        if slot in R32_SOURCES:
            pos_a, pos_b = R32_SOURCES[slot]
            ta = _resolve_pos(pos_a)
            tb = _resolve_pos(pos_b)
            return (ta if ta in all_teams else None), (tb if tb in all_teams else None)
        feeders = BRACKET_FEEDERS.get(slot)
        if not feeders:
            return None, None
        a, b = feeders
        ta = saved_ko_preds.get(a, {}).get("predicted_winner")
        tb = saved_ko_preds.get(b, {}).get("predicted_winner")
        return (ta if ta and ta in all_teams else None), (tb if tb and tb in all_teams else None)

    def _matchup(slot: str) -> str:
        """Returns HTML 'Team A vs Team B': from group preds for R32, from KO picks for later rounds."""
        # R32: derive from group stage predictions
        if slot in R32_SOURCES:
            pos_a, pos_b = R32_SOURCES[slot]
            ta, tb = _resolve_pos(pos_a), _resolve_pos(pos_b)
            return f"{flag_img(ta)}<b>{ta}</b>&nbsp;&nbsp;vs&nbsp;&nbsp;{flag_img(tb)}<b>{tb}</b>"
        # R16+: cascade from saved knockout picks
        feeders = BRACKET_FEEDERS.get(slot)
        if not feeders:
            return ""
        a, b = feeders
        ta = saved_ko_preds.get(a, {}).get("predicted_winner") or f"winner of {SLOT_NAMES.get(a, a)}"
        tb = saved_ko_preds.get(b, {}).get("predicted_winner") or f"winner of {SLOT_NAMES.get(b, b)}"
        return f"{flag_img(ta)}<b>{ta}</b>&nbsp;&nbsp;vs&nbsp;&nbsp;{flag_img(tb)}<b>{tb}</b>"

    BRACKET_ROUNDS = [
        ("Round of 32",    [f"R32_{i}" for i in range(1, 17)], 2,  4),
        ("Round of 16",    [f"R16_{i}" for i in range(1, 9)],  4,  4),
        ("Quarter-Finals", [f"QF_{i}"  for i in range(1, 5)],  6,  4),
        ("Semi-Finals",    ["SF_1", "SF_2"],                    8,  2),
        ("3rd Place Match",["THIRD_PLACE"],                     5,  1),
        ("Final 🏆",       ["FINAL"],                           15, 1),
    ]

    for round_name, slots, pts, n_cols in BRACKET_ROUNDS:
        st.subheader(f"{round_name} — {pts} pts per correct pick")

        with st.form(f"ko_{round_name.replace(' ', '_')}"):
            picks: dict[str, str] = {}
            cols = st.columns(n_cols)

            for i, slot in enumerate(slots):
                existing_val = saved_ko_preds.get(slot, {}).get("predicted_winner")
                matchup = _matchup(slot)

                with cols[i % n_cols]:
                    label = SLOT_NAMES.get(slot, slot)
                    if matchup:
                        st.markdown(f"**{label}**", unsafe_allow_html=False)
                        st.markdown(matchup, unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{label}**")

                    ta, tb = _slot_teams(slot)
                    slot_opts = ["\u2014 Select team \u2014", ta, tb] if ta and tb else team_options
                    pick = st.selectbox(
                        "Who wins?", slot_opts,
                        index=_team_idx(existing_val, slot_opts),
                        disabled=locked, key=f"kp_{slot}",
                        label_visibility="collapsed",
                    )
                    picks[slot] = pick

            submitted_ko = st.form_submit_button(
                f"💾 Save {round_name}", disabled=locked
            )

        if submitted_ko and not locked:
            missing = [s for s, v in picks.items() if v == "— Select team —"]
            if missing:
                st.error(f"Please select a team for every match.")
            else:
                with st.spinner(f"Saving {round_name}..."):
                    for slot, team in picks.items():
                        upsert_knockout_pred(user["id"], slot, team)
                    get_user_knockout_preds.clear()
                st.success(f"✅ {round_name} saved.")

        st.divider()
