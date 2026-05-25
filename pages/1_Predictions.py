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
teams_by_group = get_teams_by_group()
matches_by_group = get_group_matches()
saved_bets = get_user_bets(user["id"])
saved_group_preds = get_user_group_preds(user["id"])
saved_ko_preds = get_user_knockout_preds(user["id"])
group_names = sorted(matches_by_group.keys())

_WINNER_TO_IDX = {"home": 0, "draw": 1, "away": 2}


def _completion_icon(group: str) -> str:
    matches = matches_by_group.get(group, [])
    n_saved = sum(1 for m in matches if m["id"] in saved_bets)
    if n_saved == len(matches):
        return " ✅"
    if n_saved > 0:
        return " ⚠️"
    return ""


# ── Tabs: one per group + Knockout ────────────────────────────────────────────
tab_labels = [f"Group {g}{_completion_icon(g)}" for g in group_names] + ["🎯 Knockout"]
tabs = st.tabs(tab_labels)

# ── Group tabs ─────────────────────────────────────────────────────────────────
for tab, group in zip(tabs[:-1], group_names):
    with tab:
        matches = matches_by_group[group]
        teams = teams_by_group.get(group, [])

        teams_html = " · ".join(f'{flag_img(t)}{t}' for t in teams)
        st.markdown(f"Teams: {teams_html}", unsafe_allow_html=True)

        with st.form(f"form_{group}"):
            batch: dict[int, tuple[str, int, int]] = {}

            for match in matches:
                mid = match["id"]
                home = match["home_team"]
                away = match["away_team"]
                date_str = match["match_date"]
                existing = saved_bets.get(mid, {})

                st.markdown(
                    f'{flag_img(home)}<b>{home}</b> vs {flag_img(away)}<b>{away}</b>'
                    f' &mdash; {date_str[:10]} {date_str[11:16]} UTC',
                    unsafe_allow_html=True,
                )

                options = [f"{home} wins", "Draw", f"{away} wins"]
                default_idx = _WINNER_TO_IDX.get(
                    existing.get("predicted_winner", "home"), 0
                )

                col_radio, col_hs, col_as = st.columns([4, 1, 1])
                with col_radio:
                    winner_label = st.radio(
                        "Result", options,
                        index=default_idx, horizontal=True,
                        disabled=locked, key=f"w_{mid}",
                        label_visibility="collapsed",
                    )
                with col_hs:
                    hs = st.number_input(
                        home, min_value=0, max_value=20,
                        value=existing.get("predicted_home_score") or 0,
                        step=1, disabled=locked, key=f"hs_{mid}",
                    )
                with col_as:
                    as_ = st.number_input(
                        away, min_value=0, max_value=20,
                        value=existing.get("predicted_away_score") or 0,
                        step=1, disabled=locked, key=f"as_{mid}",
                    )

                if winner_label == options[0]:
                    winner_code = "home"
                elif winner_label == options[1]:
                    winner_code = "draw"
                else:
                    winner_code = "away"

                batch[mid] = (winner_code, int(hs), int(as_))
                st.divider()

            submitted = st.form_submit_button(
                f"💾 Save Group {group}", disabled=locked
            )

        if submitted and not locked:
            for mid, (w, hs_val, as_val) in batch.items():
                upsert_bet(user["id"], mid, w, hs_val, as_val)
            derive_and_save_group_prediction(user["id"], group)
            get_user_bets.clear()
            get_user_group_preds.clear()
            st.success(
                f"✅ Group {group} saved — {len(batch)} matches predicted, "
                "group standings derived automatically."
            )
            st.rerun()

# ── Knockout tab ───────────────────────────────────────────────────────────────
with tabs[-1]:
    if locked:
        st.warning("🔒 Predictions are locked.")
    else:
        st.info(
            "Predict who wins each match. "
            "Once you save a round, the **next round shows who you predicted** "
            "to face each other — so the bracket builds itself."
        )

    all_teams = sorted(t for teams in teams_by_group.values() for t in teams)
    team_options = ["— Select team —"] + all_teams

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
            groups = "/".join(pos[1:])
            return f"Best 3rd ({groups})"
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
                for slot, team in picks.items():
                    upsert_knockout_pred(user["id"], slot, team)
                get_user_knockout_preds.clear()
                st.success(f"✅ {round_name} saved.")
                st.rerun()

        st.divider()
