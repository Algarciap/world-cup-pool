"""
Comprehensive test suite for the ESPN API sync integration.

Tests:
  1. API connectivity
  2. Full schedule coverage (all 48 group stage matches present)
  3. Team name mapping (every ESPN name resolves to a known DB team)
  4. Response structure (scores accessible after a match finishes)
  5. Dry-run sync against the real DB (read-only — no writes)

Run with:
    py scripts/test_espn.py
"""

import sys
import os
import json
import requests
from datetime import date, timedelta

# Allow importing db.py from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import _normalize_espn_name, TEAM_FLAGS, _client

# ── Helpers ────────────────────────────────────────────────────────────────────

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

# ── Test 1: API connectivity ───────────────────────────────────────────────────

section("TEST 1 — ESPN API connectivity")

url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
try:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    events_today = data.get("events", [])
    print(f"{PASS} Reachable  (HTTP {r.status_code})")
    print(f"   Events returned (no date filter): {len(events_today)}")
    for e in events_today:
        comp = e["competitions"][0]
        names = [c["team"]["displayName"] for c in comp["competitors"]]
        status = comp["status"]["type"]["name"]
        print(f"   • {' vs '.join(names)}  [{status}]")
except Exception as exc:
    print(f"{FAIL} ESPN unreachable: {exc}")
    sys.exit(1)

# ── Test 2: Full schedule sweep ────────────────────────────────────────────────

section("TEST 2 — Full WC 2026 schedule coverage")

espn_matches: list[dict] = []   # {date, home, away, status, home_score, away_score}
espn_names_seen: set[str] = set()

d = date(2026, 6, 11)
end = date(2026, 7, 20)
while d <= end:
    ds = d.strftime("%Y%m%d")
    url_d = (
        "https://site.api.espn.com/apis/site/v2/sports/soccer"
        f"/fifa.world/scoreboard?dates={ds}&limit=50"
    )
    r = requests.get(url_d, timeout=10)
    for e in r.json().get("events", []):
        comp = e["competitions"][0]
        competitors = comp.get("competitors", [])
        home_c = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away_c = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home_c or not away_c:
            continue
        home_raw = home_c["team"]["displayName"]
        away_raw = away_c["team"]["displayName"]
        espn_names_seen.add(home_raw)
        espn_names_seen.add(away_raw)
        status_type = comp["status"]["type"]
        espn_matches.append({
            "date": ds,
            "home_raw": home_raw,
            "away_raw": away_raw,
            "home": _normalize_espn_name(home_raw),
            "away": _normalize_espn_name(away_raw),
            "completed": status_type.get("completed", False),
            "status": status_type.get("name", "?"),
            "home_score": home_c.get("score"),
            "away_score": away_c.get("score"),
        })
    d += timedelta(days=1)

# Filter to real-team matches (exclude placeholders like "Group A Winner")
db_teams = set(TEAM_FLAGS.keys())
real_matches = [
    m for m in espn_matches
    if m["home"] in db_teams and m["away"] in db_teams
]
placeholder_matches = [m for m in espn_matches if m not in real_matches]

print(f"   Total ESPN matches found      : {len(espn_matches)}")
print(f"   Real-team matches             : {len(real_matches)}")
print(f"   Placeholder/TBD matches       : {len(placeholder_matches)}")

group_matches = [m for m in real_matches if m["date"] <= "20260702"]
# WC 2026 has 48 teams → 12 groups × 6 matches = 72 group stage matches
if len(group_matches) == 72:
    print(f"{PASS} All 72 group stage matches present")
else:
    print(f"{WARN} Expected 72 group stage matches, found {len(group_matches)}")

completed = [m for m in real_matches if m["completed"]]
upcoming  = [m for m in real_matches if not m["completed"]]
print(f"   Completed matches so far      : {len(completed)}")
print(f"   Upcoming/scheduled            : {len(upcoming)}")

# ── Test 3: Team name mapping ──────────────────────────────────────────────────

section("TEST 3 — Team name mapping (ESPN → DB)")

# Only check names that are actual country names, not placeholders
real_espn_names = {
    n for n in espn_names_seen
    if not any(kw in n for kw in ("Winner", "Loser", "Place", "Group", "Semifinal",
                                   "Quarterfinal", "Round"))
}

unmapped = []
for name in sorted(real_espn_names):
    mapped = _normalize_espn_name(name)
    if mapped not in db_teams:
        unmapped.append((name, mapped))

if not unmapped:
    print(f"{PASS} All {len(real_espn_names)} ESPN team names map to a known DB team")
else:
    print(f"{FAIL} {len(unmapped)} ESPN name(s) do NOT map to any DB team:")
    for espn, mapped in unmapped:
        print(f"   ESPN: '{espn}'  →  mapped: '{mapped}'  (not in DB)")
    print("\n   DB team list for reference:")
    for t in sorted(db_teams):
        print(f"     {t}")

# ── Test 4: Response structure for a completed match ──────────────────────────

section("TEST 4 — Score fields on a completed match")

def _check_scores(matches: list[dict], label: str) -> bool:
    """Return True if all completed matches in the list have parseable scores."""
    ok = True
    for m in matches:
        hs, as_ = m["home_score"], m["away_score"]
        if hs is None or as_ is None:
            print(f"{FAIL} [{label}] Missing score: {m['home']} vs {m['away']}")
            ok = False
            continue
        try:
            int(hs); int(as_)
        except (ValueError, TypeError):
            print(f"{FAIL} [{label}] Non-numeric score: home={hs!r} away={as_!r}")
            ok = False
    return ok

if completed:
    # Use live WC 2026 completed matches
    if _check_scores(completed, "WC 2026 live"):
        sample = completed[0]
        print(f"{PASS} WC 2026 live scores OK — "
              f"sample: {sample['home']} {int(sample['home_score'])}–"
              f"{int(sample['away_score'])} {sample['away']}")
else:
    # Tournament hasn't started yet — validate using WC 2022 historical data
    # from the same ESPN endpoint (confirmed to return real completed results)
    print(f"   WC 2026 not started — running against WC 2022 historical data…")
    WC2022_DATES = ["20221120", "20221121", "20221122"]  # opening 3 days
    wc22_matches: list[dict] = []
    for ds in WC2022_DATES:
        url_22 = (
            "https://site.api.espn.com/apis/site/v2/sports/soccer"
            f"/fifa.world/scoreboard?dates={ds}&limit=20"
        )
        r22 = requests.get(url_22, timeout=10)
        for e in r22.json().get("events", []):
            comp = e["competitions"][0]
            if not comp["status"]["type"].get("completed"):
                continue
            competitors = comp.get("competitors", [])
            home_c = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away_c = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if home_c and away_c:
                wc22_matches.append({
                    "date": ds,
                    "home": home_c["team"]["displayName"],
                    "away": away_c["team"]["displayName"],
                    "completed": True,
                    "home_score": home_c.get("score"),
                    "away_score": away_c.get("score"),
                })

    if not wc22_matches:
        print(f"{FAIL} Could not fetch WC 2022 historical data for score test")
    elif _check_scores(wc22_matches, "WC 2022 historical"):
        print(f"{PASS} Score fields valid on {len(wc22_matches)} WC 2022 historical match(es):")
        for m in wc22_matches:
            print(f"   • {m['home']} {int(m['home_score'])}–{int(m['away_score'])} {m['away']}  ({m['date']})")

# ── Test 5: Dry-run sync against real DB ──────────────────────────────────────

section("TEST 5 — Dry-run sync against Supabase DB (read-only)")

try:
    db = _client()
    db_upcoming = (
        db.table("matches")
        .select("id, home_team, away_team, match_date, status")
        .eq("status", "upcoming")
        .execute()
        .data
    )
    print(f"   Upcoming matches in DB: {len(db_upcoming)}")

    espn_lookup = {(m["home"], m["away"]): m for m in real_matches if m["completed"]}

    would_sync = []
    would_skip = []
    for m in db_upcoming:
        key = (m["home_team"], m["away_team"])
        if key in espn_lookup:
            r = espn_lookup[key]
            would_sync.append(
                f"{m['home_team']} {r['home_score']}–{r['away_score']} {m['away_team']}"
            )
        else:
            would_skip.append(f"{m['home_team']} vs {m['away_team']}")

    if would_sync:
        print(f"{PASS} Would sync {len(would_sync)} result(s):")
        for s in would_sync:
            print(f"   • {s}")
    else:
        print(f"{PASS} No completed results to sync yet (tournament hasn't started)")

    if would_skip:
        print(f"   Would skip {len(would_skip)} match(es) (not yet finished on ESPN)")

except Exception as exc:
    print(f"{FAIL} Could not connect to Supabase: {exc}")
    print(f"   Make sure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in .env")

# ── Summary ────────────────────────────────────────────────────────────────────

section("SUMMARY")
print(f"   ESPN matches found     : {len(espn_matches)}")
print(f"   Real-team matches      : {len(real_matches)}")
print(f"   Unmapped team names    : {len(unmapped)}")
print(f"   Completed (live data)  : {len(completed)}")
if not unmapped:
    print(f"\n{PASS} Sync is ready — all team names map correctly.")
else:
    print(f"\n{FAIL} Fix the unmapped team names above before the tournament starts.")
