"""
db.py — Supabase data access layer for the World Cup 2026 pool.

All DB calls use the service-role key so they bypass RLS and work
regardless of Supabase Auth session state.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env for local development; Streamlit Cloud uses st.secrets instead
load_dotenv(Path(__file__).parent / ".env")

def _secret(key: str) -> str:
    """Read from Streamlit secrets (Cloud) or fall back to environment variable."""
    try:
        return st.secrets[key]
    except (FileNotFoundError, KeyError):
        return os.getenv(key, "")

# Bets are locked when the tournament kicks off (Mexico vs South Africa)
LOCK_DT = datetime(2026, 6, 11, 19, 0, 0, tzinfo=timezone.utc)

# ── Flag emojis ────────────────────────────────────────────────────────────────
TEAM_FLAGS: dict[str, str] = {
    # Group A
    "Mexico": "🇲🇽", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Czech Republic": "🇨🇿",
    # Group B
    "Canada": "🇨🇦", "Bosnia and Herzegovina": "🇧🇦", "Qatar": "🇶🇦", "Switzerland": "🇨🇭",
    # Group C
    "Brazil": "🇧🇷", "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    # Group D
    "United States": "🇺🇸", "Paraguay": "🇵🇾", "Australia": "🇦🇺", "Turkey": "🇹🇷",
    # Group E
    "Germany": "🇩🇪", "Curaçao": "🇨🇼", "Ivory Coast": "🇨🇮", "Ecuador": "🇪🇨",
    # Group F
    "Netherlands": "🇳🇱", "Japan": "🇯🇵", "Sweden": "🇸🇪", "Tunisia": "🇹🇳",
    # Group G
    "Belgium": "🇧🇪", "Egypt": "🇪🇬", "Iran": "🇮🇷", "New Zealand": "🇳🇿",
    # Group H
    "Spain": "🇪🇸", "Cape Verde": "🇨🇻", "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾",
    # Group I
    "France": "🇫🇷", "Senegal": "🇸🇳", "Iraq": "🇮🇶", "Norway": "🇳🇴",
    # Group J
    "Argentina": "🇦🇷", "Algeria": "🇩🇿", "Austria": "🇦🇹", "Jordan": "🇯🇴",
    # Group K
    "Portugal": "🇵🇹", "DR Congo": "🇨🇩", "Uzbekistan": "🇺🇿", "Colombia": "🇨🇴",
    # Group L
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Croatia": "🇭🇷", "Ghana": "🇬🇭", "Panama": "🇵🇦",
}


def with_flag(team: str) -> str:
    """Returns 'flag team', e.g. '🇧🇷 Brazil'. Falls back to plain name."""
    f = TEAM_FLAGS.get(team, "")
    return f"{f} {team}" if f else team


# ISO 3166-1 alpha-2 codes for flagcdn.com
TEAM_CODES: dict[str, str] = {
    "Mexico": "mx", "South Africa": "za", "South Korea": "kr", "Czech Republic": "cz",
    "Canada": "ca", "Bosnia and Herzegovina": "ba", "Qatar": "qa", "Switzerland": "ch",
    "Brazil": "br", "Morocco": "ma", "Haiti": "ht", "Scotland": "gb-sct",
    "United States": "us", "Paraguay": "py", "Australia": "au", "Turkey": "tr",
    "Germany": "de", "Curaçao": "cw", "Ivory Coast": "ci", "Ecuador": "ec",
    "Netherlands": "nl", "Japan": "jp", "Sweden": "se", "Tunisia": "tn",
    "Belgium": "be", "Egypt": "eg", "Iran": "ir", "New Zealand": "nz",
    "Spain": "es", "Cape Verde": "cv", "Saudi Arabia": "sa", "Uruguay": "uy",
    "France": "fr", "Senegal": "sn", "Iraq": "iq", "Norway": "no",
    "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Jordan": "jo",
    "Portugal": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co",
    "England": "gb-eng", "Croatia": "hr", "Ghana": "gh", "Panama": "pa",
}


def flag_img(team: str, height: int = 20) -> str:
    """Returns an HTML <img> flag for use with unsafe_allow_html=True."""
    code = TEAM_CODES.get(team, "")
    if not code:
        return ""
    return (
        f'<img src="https://flagcdn.com/h{height}/{code}.png" '
        f'height="{height}" style="vertical-align:middle; margin-right:4px;">'
    )


# Valid office values
OFFICES: list[str] = ["Spain", "Malta", "South Africa", "Nigeria", "Zambia", "UK"]


def is_locked() -> bool:
    return datetime.now(timezone.utc) >= LOCK_DT


def _client() -> Client:
    url = _secret("SUPABASE_URL")
    key = _secret("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Missing Supabase credentials. Add SUPABASE_URL and "
            "SUPABASE_SERVICE_KEY to Streamlit Cloud secrets or .env file."
        )
    return create_client(url, key)


# ── Users ──────────────────────────────────────────────────────────────────────

def get_or_create_user(name: str, email: str, office: str | None = None) -> dict:
    """Returns the existing user row or creates a new one.

    If the user already exists but has no office set, and an office is supplied,
    the office is saved to the DB and returned in the result dict.
    """
    db = _client()
    email = email.strip().lower()
    result = db.table("users").select("*").eq("email", email).execute()
    if result.data:
        user = result.data[0]
        if office and not user.get("office"):
            db.table("users").update({"office": office}).eq("id", user["id"]).execute()
            user["office"] = office
        return user
    payload: dict = {"name": name.strip(), "email": email}
    if office:
        payload["office"] = office
    result = db.table("users").insert(payload).execute()
    return result.data[0]


def update_user_office(user_id: str, office: str) -> None:
    """Update the office field for an existing user."""
    db = _client()
    db.table("users").update({"office": office}).eq("id", user_id).execute()


def get_user_by_email(email: str) -> dict | None:
    """Look up a user by email without creating one. Returns None if not found."""
    db = _client()
    result = db.table("users").select("*").eq("email", email.strip().lower()).execute()
    return result.data[0] if result.data else None


def get_completion_stats() -> dict:
    """Returns {'total': N, 'completed': M} — users who have all 12 group predictions."""
    from collections import Counter
    db = _client()
    users_res = db.table("users").select("id").execute()
    total = len(users_res.data)
    if total == 0:
        return {"total": 0, "completed": 0}
    gp_res = db.table("group_predictions").select("user_id").execute()
    counts = Counter(row["user_id"] for row in gp_res.data)
    completed = sum(1 for c in counts.values() if c >= 12)
    return {"total": total, "completed": completed}


def get_all_users() -> list[dict]:
    db = _client()
    return db.table("users").select("*").order("name").execute().data


# ── Teams ──────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def get_teams_by_group() -> dict[str, list[str]]:
    """Returns {group_name: [team_name, ...]} sorted alphabetically."""
    db = _client()
    rows = (
        db.table("teams")
        .select("name, group_name")
        .order("group_name")
        .order("name")
        .execute()
        .data
    )
    groups: dict[str, list[str]] = {}
    for row in rows:
        groups.setdefault(row["group_name"], []).append(row["name"])
    return groups


# ── Matches ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_group_matches() -> dict[str, list[dict]]:
    """Returns group-stage matches keyed by group_name, ordered by date."""
    db = _client()
    rows = (
        db.table("matches")
        .select("*")
        .eq("stage", "group")
        .order("match_date")
        .execute()
        .data
    )
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["group_name"], []).append(row)
    return groups


def get_all_matches() -> list[dict]:
    db = _client()
    return db.table("matches").select("*").order("match_date").execute().data


# ── Match bets (group stage) ───────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def get_user_bets(user_id: str) -> dict[int, dict]:
    """Returns {match_id: bet_row} for the given user."""
    db = _client()
    rows = db.table("bets").select("*").eq("user_id", user_id).execute().data
    return {row["match_id"]: row for row in rows}


def upsert_bet(
    user_id: str,
    match_id: int,
    predicted_winner: str,
    predicted_home_score: int | None = None,
    predicted_away_score: int | None = None,
) -> None:
    db = _client()
    db.table("bets").upsert(
        {
            "user_id": user_id,
            "match_id": match_id,
            "predicted_winner": predicted_winner,
            "predicted_home_score": predicted_home_score,
            "predicted_away_score": predicted_away_score,
        },
        on_conflict="user_id,match_id",
    ).execute()


# ── Group predictions ──────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def get_user_group_preds(user_id: str) -> dict[str, dict]:
    """Returns {group_name: prediction_row} for the given user."""
    db = _client()
    rows = (
        db.table("group_predictions")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    return {row["group_name"]: row for row in rows}


def derive_and_save_group_prediction(user_id: str, group_name: str) -> None:
    """Auto-derives implied group standings from the user's match predictions
    and persists them to group_predictions.  Called after saving match bets."""
    db = _client()
    matches = (
        db.table("matches")
        .select("id, home_team, away_team")
        .eq("group_name", group_name)
        .execute()
        .data
    )
    # Bypass the @st.cache_data wrapper so we always read the freshly-written rows
    bets_rows = db.table("bets").select("*").eq("user_id", user_id).execute().data
    bets: dict[int, dict] = {row["match_id"]: row for row in bets_rows}

    # Accumulate points + goals for tiebreaker (GD, then GF)
    stats: dict[str, dict] = {}
    for m in matches:
        h, a = m["home_team"], m["away_team"]
        for t in (h, a):
            stats.setdefault(t, {"pts": 0, "gf": 0, "ga": 0})
        bet = bets.get(m["id"])
        if not bet:
            continue
        hs = bet.get("predicted_home_score") or 0
        as_ = bet.get("predicted_away_score") or 0
        stats[h]["gf"] += hs
        stats[h]["ga"] += as_
        stats[a]["gf"] += as_
        stats[a]["ga"] += hs
        if bet["predicted_winner"] == "home":
            stats[h]["pts"] += 3
        elif bet["predicted_winner"] == "away":
            stats[a]["pts"] += 3
        else:
            stats[h]["pts"] += 1
            stats[a]["pts"] += 1

    if len(stats) < 4:
        return  # group hasn't been fully initialised yet

    # Only save if all matches in the group are predicted
    if sum(1 for m in matches if m["id"] in bets) < len(matches):
        return

    standings = sorted(
        stats.keys(),
        key=lambda t: (stats[t]["pts"], stats[t]["gf"] - stats[t]["ga"], stats[t]["gf"]),
        reverse=True,
    )
    db.table("group_predictions").upsert(
        {
            "user_id": user_id,
            "group_name": group_name,
            "first_place": standings[0],
            "second_place": standings[1],
            "third_place": standings[2],
        },
        on_conflict="user_id,group_name",
    ).execute()


def upsert_group_pred(
    user_id: str,
    group_name: str,
    first_place: str,
    second_place: str,
    third_place: str,
) -> None:
    db = _client()
    db.table("group_predictions").upsert(
        {
            "user_id": user_id,
            "group_name": group_name,
            "first_place": first_place,
            "second_place": second_place,
            "third_place": third_place,
        },
        on_conflict="user_id,group_name",
    ).execute()


# ── Knockout predictions ───────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def get_user_knockout_preds(user_id: str) -> dict[str, dict]:
    """Returns {slot: prediction_row} for the given user."""
    db = _client()
    rows = (
        db.table("knockout_predictions")
        .select("*")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    return {row["slot"]: row for row in rows}


def upsert_knockout_pred(user_id: str, slot: str, predicted_winner: str) -> None:
    db = _client()
    db.table("knockout_predictions").upsert(
        {
            "user_id": user_id,
            "slot": slot,
            "predicted_winner": predicted_winner,
        },
        on_conflict="user_id,slot",
    ).execute()


# ── Leaderboard ────────────────────────────────────────────────────────────────

def get_leaderboard() -> list[dict]:
    db = _client()
    return db.table("leaderboard").select("*").execute().data


def get_office_summary(leaderboard_rows: list[dict]) -> list[dict]:
    """Returns per-office stats derived from already-fetched leaderboard rows.

    Each entry: {office, participants, avg_score, top_scorer, top_score}
    """
    if not leaderboard_rows:
        return []
    from collections import defaultdict
    buckets: dict[str, list] = defaultdict(list)
    for r in leaderboard_rows:
        o = r.get("office") or "Unknown"
        buckets[o].append(r)
    summary = []
    for o in OFFICES + (["Unknown"] if "Unknown" in buckets else []):
        members = buckets.get(o)
        if not members:
            continue
        avg_score = sum(m["total_points"] for m in members) / len(members)
        top = max(members, key=lambda m: m["total_points"])
        summary.append({
            "office": o,
            "participants": len(members),
            "avg_score": round(avg_score, 1),
            "top_scorer": top["name"],
            "top_score": top["total_points"],
        })
    return summary


def get_all_users_predictions() -> dict:
    """Returns all users with their group + knockout predictions (for Others page)."""
    db = _client()
    users = db.table("users").select("id, name").order("name").execute().data
    group_preds = db.table("group_predictions").select("*").execute().data
    ko_preds = db.table("knockout_predictions").select("*").execute().data

    by_user_group: dict[str, dict[str, dict]] = {}
    for p in group_preds:
        by_user_group.setdefault(p["user_id"], {})[p["group_name"]] = p

    by_user_ko: dict[str, dict[str, dict]] = {}
    for p in ko_preds:
        by_user_ko.setdefault(p["user_id"], {})[p["slot"]] = p

    return {"users": users, "group_preds": by_user_group, "ko_preds": by_user_ko}


# ── Admin: match results & point calculation ───────────────────────────────────

def update_match_result(match_id: int, home_score: int, away_score: int) -> None:
    """Marks a match finished and immediately calculates points for all bets."""
    db = _client()

    if home_score > away_score:
        actual = "home"
    elif away_score > home_score:
        actual = "away"
    else:
        actual = "draw"

    db.table("matches").update(
        {"home_score": home_score, "away_score": away_score, "status": "finished"}
    ).eq("id", match_id).execute()

    bets = db.table("bets").select("*").eq("match_id", match_id).execute().data
    for bet in bets:
        pts = 0
        if bet["predicted_winner"] == actual:
            pts += 3
            if (
                bet["predicted_home_score"] == home_score
                and bet["predicted_away_score"] == away_score
            ):
                pts += 2
        db.table("bets").update({"points_earned": pts}).eq("id", bet["id"]).execute()


def calculate_group_points(group_name: str) -> None:
    """Awards group-prediction points once all 6 group matches are finished."""
    db = _client()
    finished = (
        db.table("matches")
        .select("*")
        .eq("group_name", group_name)
        .eq("status", "finished")
        .execute()
        .data
    )
    if len(finished) < 6:
        return  # group not yet complete

    pts: dict[str, int] = {}
    gd: dict[str, int] = {}
    gf: dict[str, int] = {}

    for m in finished:
        h, a = m["home_team"], m["away_team"]
        hs, as_ = m["home_score"], m["away_score"]
        for team in (h, a):
            pts.setdefault(team, 0)
            gd.setdefault(team, 0)
            gf.setdefault(team, 0)
        gf[h] += hs
        gf[a] += as_
        gd[h] += hs - as_
        gd[a] += as_ - hs
        if hs > as_:
            pts[h] += 3
        elif as_ > hs:
            pts[a] += 3
        else:
            pts[h] += 1
            pts[a] += 1

    standings = sorted(
        pts.keys(), key=lambda t: (pts[t], gd[t], gf[t]), reverse=True
    )
    actual_1st = standings[0] if len(standings) > 0 else None
    actual_2nd = standings[1] if len(standings) > 1 else None
    actual_3rd = standings[2] if len(standings) > 2 else None

    preds = (
        db.table("group_predictions")
        .select("*")
        .eq("group_name", group_name)
        .execute()
        .data
    )
    for pred in preds:
        p = 0
        if pred["first_place"] == actual_1st:
            p += 4
        if pred["second_place"] == actual_2nd:
            p += 3
        if pred["third_place"] == actual_3rd:
            p += 2
        db.table("group_predictions").update({"points_earned": p}).eq("id", pred["id"]).execute()


# Points awarded per correct prediction by knockout round
_KNOCKOUT_PTS: dict[str, int] = {
    "R32": 2,
    "R16": 4,
    "QF": 6,
    "SF": 8,
    "THIRD": 5,
    "FINAL": 15,
}


def calculate_knockout_points(slot: str, actual_winner: str) -> None:
    """Awards knockout-prediction points after a knockout match result is known."""
    db = _client()
    # Derive round prefix from slot name (e.g. "R32_1" → "R32", "FINAL" → "FINAL")
    prefix = slot.split("_")[0]
    pts_for_correct = _KNOCKOUT_PTS.get(prefix, 2)

    preds = (
        db.table("knockout_predictions")
        .select("*")
        .eq("slot", slot)
        .execute()
        .data
    )
    for pred in preds:
        p = pts_for_correct if pred["predicted_winner"] == actual_winner else 0
        db.table("knockout_predictions").update({"points_earned": p}).eq("id", pred["id"]).execute()


# ── ESPN result sync ───────────────────────────────────────────────────────────

# Maps ESPN display names → team names used in this app's DB.
_ESPN_NAME_ALIASES: dict[str, str] = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Democratic Republic of Congo": "DR Congo",
    "Congo DR": "DR Congo",
    "Cape Verde Islands": "Cape Verde",
    "USA": "United States",
    "Curacao": "Curaçao",
    "Korea Republic": "South Korea",
    # Confirmed from live ESPN WC 2026 schedule sweep
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
}


def _normalize_espn_name(name: str) -> str:
    return _ESPN_NAME_ALIASES.get(name, name)


def sync_results_from_espn() -> dict:
    """Fetches completed match results from ESPN and writes them to the DB.

    Only processes matches currently marked 'upcoming' in the DB.
    Returns {"synced": N, "skipped": M, "errors": [...]}.
    """
    import requests

    db = _client()

    # Only look at matches we haven't marked finished yet
    upcoming = (
        db.table("matches")
        .select("*")
        .eq("status", "upcoming")
        .execute()
        .data
    )
    if not upcoming:
        return {"synced": 0, "skipped": 0, "errors": []}

    # Collect the unique calendar dates (YYYYMMDD) across all upcoming matches
    date_strs = {m["match_date"][:10].replace("-", "") for m in upcoming}

    # Build a lookup of ESPN-confirmed finished results keyed by (home, away)
    espn_results: dict[tuple[str, str], tuple[int, int]] = {}
    errors: list[str] = []

    for date_str in sorted(date_strs):
        url = (
            "https://site.api.espn.com/apis/site/v2/sports/soccer"
            f"/fifa.world/scoreboard?dates={date_str}&limit=50"
        )
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            errors.append(f"ESPN fetch failed for {date_str}: {exc}")
            continue

        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            if not competition.get("status", {}).get("type", {}).get("completed"):
                continue
            competitors = competition.get("competitors", [])
            home_c = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away_c = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if not home_c or not away_c:
                continue
            home_name = _normalize_espn_name(home_c["team"]["displayName"])
            away_name = _normalize_espn_name(away_c["team"]["displayName"])
            try:
                hs = int(home_c.get("score", 0))
                as_ = int(away_c.get("score", 0))
            except (ValueError, TypeError):
                continue
            espn_results[(home_name, away_name)] = (hs, as_)

    # Apply results to the DB
    synced = 0
    skipped = 0
    groups_updated: set[str] = set()
    ko_slots_updated: list[tuple[str, str]] = []

    for match in upcoming:
        key = (match["home_team"], match["away_team"])
        if key not in espn_results:
            skipped += 1
            continue
        hs, as_ = espn_results[key]
        try:
            update_match_result(match["id"], hs, as_)
            if match.get("group_name"):
                groups_updated.add(match["group_name"])
            if match.get("slot"):
                winner = match["home_team"] if hs > as_ else match["away_team"]
                ko_slots_updated.append((match["slot"], winner))
            synced += 1
        except Exception as exc:
            errors.append(f"{match['home_team']} vs {match['away_team']}: {exc}")

    # Recalculate group / knockout prediction points after all results are in
    for group in groups_updated:
        calculate_group_points(group)
    for slot, winner in ko_slots_updated:
        calculate_knockout_points(slot, winner)

    return {"synced": synced, "skipped": skipped, "errors": errors}
