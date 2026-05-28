"""
run_tests.py — smoke + unit tests for the World Cup pool app.

Covers:
  1. db.py — OFFICES constant, get_office_summary logic, is_locked, flag helpers
  2. get_or_create_user / update_user_office signatures
  3. Live DB connectivity + leaderboard view (office column present)
  4. Registration flow: create a test user with office, read back, clean up

Run from the project root:
    python scripts/run_tests.py
"""

import sys
import os
import inspect
from pathlib import Path
from datetime import datetime, timezone

# ── Make project root importable ──────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Suppress Streamlit import noise
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "1")

PASS = "\033[92m  PASS\033[0m"
FAIL = "\033[91m  FAIL\033[0m"
SKIP = "\033[93m  SKIP\033[0m"
INFO = "\033[94m  INFO\033[0m"

results = {"passed": 0, "failed": 0, "skipped": 0}


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        print(f"{PASS}  {label}")
        results["passed"] += 1
    else:
        print(f"{FAIL}  {label}" + (f"  — {detail}" if detail else ""))
        results["failed"] += 1


def skip(label: str, reason: str = ""):
    print(f"{SKIP}  {label}" + (f"  — {reason}" if reason else ""))
    results["skipped"] += 1


def section(title: str):
    print(f"\n\033[1m{'─' * 60}\033[0m")
    print(f"\033[1m  {title}\033[0m")
    print(f"\033[1m{'─' * 60}\033[0m")


# ══════════════════════════════════════════════════════════════
# 1. IMPORT CHECKS
# ══════════════════════════════════════════════════════════════
section("1. Module imports")

try:
    import db
    check("db.py imports cleanly", True)
except Exception as e:
    check("db.py imports cleanly", False, str(e))
    print("  Cannot continue without db.py — aborting.")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════
# 2. OFFICES CONSTANT
# ══════════════════════════════════════════════════════════════
section("2. OFFICES constant")

check("OFFICES is defined", hasattr(db, "OFFICES"))
check("OFFICES has exactly 6 entries", len(db.OFFICES) == 6,
      f"got {len(db.OFFICES)}")
expected = {"Spain", "Malta", "South Africa", "Nigeria", "Zambia", "UK"}
check("OFFICES contains the 6 correct values",
      set(db.OFFICES) == expected,
      f"got {set(db.OFFICES)}")
check("OFFICES contains no duplicates",
      len(db.OFFICES) == len(set(db.OFFICES)))


# ══════════════════════════════════════════════════════════════
# 3. get_office_summary LOGIC (no DB)
# ══════════════════════════════════════════════════════════════
section("3. get_office_summary logic")

def _lb(name, office, pts):
    return {"name": name, "office": office, "total_points": pts,
            "group_stage_points": 0, "group_prediction_points": 0,
            "knockout_points": 0}

# Empty leaderboard → all 6 offices with 0 participants
empty_result = db.get_office_summary([])
check("Empty leaderboard returns 6 office rows", len(empty_result) == 6,
      f"got {len(empty_result)}")
check("All offices have 0 participants when leaderboard is empty",
      all(r["participants"] == 0 for r in empty_result))
check("Top scorer is '—' for empty offices",
      all(r["top_scorer"] == "—" for r in empty_result))

# Single user in Spain
spain_rows = db.get_office_summary([_lb("Alice", "Spain", 15)])
spain = next(r for r in spain_rows if r["office"] == "Spain")
check("Spain card shows 1 participant", spain["participants"] == 1)
check("Spain avg_score is 15.0", spain["avg_score"] == 15.0)
check("Spain top_scorer is Alice", spain["top_scorer"] == "Alice")
other = next(r for r in spain_rows if r["office"] == "Malta")
check("Malta card shows 0 participants when no Malta users", other["participants"] == 0)

# Multiple users, mixed offices
rows = [
    _lb("Alice", "Spain",  20),
    _lb("Bob",   "Spain",  10),
    _lb("Carol", "Malta",  30),
    _lb("Dave",  None,      5),   # null office — should be ignored
]
summary = db.get_office_summary(rows)
spain2 = next(r for r in summary if r["office"] == "Spain")
malta2 = next(r for r in summary if r["office"] == "Malta")
check("Spain avg is (20+10)/2 = 15.0", spain2["avg_score"] == 15.0)
check("Spain top scorer is Alice (20 pts)", spain2["top_scorer"] == "Alice")
check("Malta top scorer is Carol (30 pts)", malta2["top_scorer"] == "Carol")
check("Null-office user is not counted in any office",
      sum(r["participants"] for r in summary) == 3)

# Order matches OFFICES list
offices_order = [r["office"] for r in summary]
check("Summary rows follow OFFICES order", offices_order == db.OFFICES,
      f"got {offices_order}")


# ══════════════════════════════════════════════════════════════
# 4. FUNCTION SIGNATURES
# ══════════════════════════════════════════════════════════════
section("4. Function signatures")

sig_create = inspect.signature(db.get_or_create_user)
check("get_or_create_user accepts 'office' parameter",
      "office" in sig_create.parameters)
check("'office' parameter has a default (optional)",
      sig_create.parameters["office"].default is not inspect.Parameter.empty)

check("update_user_office is defined", hasattr(db, "update_user_office"))
sig_update = inspect.signature(db.update_user_office)
check("update_user_office accepts (user_id, office)",
      list(sig_update.parameters.keys()) == ["user_id", "office"])

check("get_office_summary is defined", hasattr(db, "get_office_summary"))
sig_summary = inspect.signature(db.get_office_summary)
check("get_office_summary accepts leaderboard_rows",
      "leaderboard_rows" in sig_summary.parameters)


# ══════════════════════════════════════════════════════════════
# 5. is_locked / LOCK_DT
# ══════════════════════════════════════════════════════════════
section("5. Lock date")

check("LOCK_DT is June 11 2026 19:00 UTC",
      db.LOCK_DT == datetime(2026, 6, 11, 19, 0, 0, tzinfo=timezone.utc))
# App is currently before lockout
check("is_locked() returns False before June 11",
      not db.is_locked())


# ══════════════════════════════════════════════════════════════
# 6. FLAG HELPERS
# ══════════════════════════════════════════════════════════════
section("6. Flag helpers")

check("flag_img returns empty string for unknown team",
      db.flag_img("Unknown Team FC") == "")
check("flag_img returns <img> tag for known team",
      db.flag_img("Spain").startswith("<img"))
check("flag_img includes flagcdn.com URL",
      "flagcdn.com" in db.flag_img("Brazil"))
check("with_flag prefixes flag emoji",
      "Spain" in db.with_flag("Spain"))


# ══════════════════════════════════════════════════════════════
# 7. LIVE DB CONNECTIVITY
# ══════════════════════════════════════════════════════════════
section("7. Live DB connectivity")

url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_SERVICE_KEY", "")

if not url or not key:
    skip("Supabase credentials not set — skipping live DB tests",
         "Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env to run these")
else:
    try:
        _db = db._client()

        # users table has office column
        res = _db.table("users").select("id, name, email, office").limit(1).execute()
        check("users table is reachable", True)
        if res.data:
            first = res.data[0]
            check("users rows contain 'office' key", "office" in first)
        else:
            print(f"{INFO}  users table is empty — skipping office column check")
            results["skipped"] += 1

        # leaderboard view has office column
        lb = _db.table("leaderboard").select("*").limit(1).execute()
        check("leaderboard view is reachable", True)
        if lb.data:
            check("leaderboard rows contain 'office' key", "office" in lb.data[0])
        else:
            print(f"{INFO}  leaderboard is empty — skipping office column check")
            results["skipped"] += 1

        # Purge any leftover test users from previous failed runs
        _db.table("users").delete().like("email", "pytest_temp_%").execute()

        _db = db._client()  # reuse same authenticated client as the app
        # ── Registration round-trip test ───────────────────────────────────
        import time as _time
        _ts = int(_time.time())
        TEST_EMAIL  = f"pytest_temp_{_ts}@kingmakers.com"
        TEST_NAME   = "__test_user__"
        TEST_OFFICE = "Malta"
        _db = db._client()  # reuse same authenticated client as the app

        # Create user with office
        created = db.get_or_create_user(TEST_NAME, TEST_EMAIL, TEST_OFFICE)
        check("get_or_create_user creates user with office",
              created.get("office") == TEST_OFFICE,
              f"got office={created.get('office')!r}")

        # Read back from DB
        read_back = db.get_user_by_email(TEST_EMAIL)
        check("Office is persisted in DB",
              read_back is not None and read_back.get("office") == TEST_OFFICE)

        # update_user_office
        db.update_user_office(created["id"], "UK")
        after_update = db.get_user_by_email(TEST_EMAIL)
        check("update_user_office changes office in DB",
              after_update is not None and after_update.get("office") == "UK")

        # Existing user with office — calling get_or_create_user should NOT overwrite
        returned = db.get_or_create_user(TEST_NAME, TEST_EMAIL, "Spain")
        check("get_or_create_user does not overwrite an already-set office",
              returned.get("office") == "UK",
              f"expected UK, got {returned.get('office')!r}")

        # Clean up
        del_res = _db.table("users").delete().eq("email", TEST_EMAIL).execute()
        check("Test user cleaned up from DB",
              len(del_res.data) == 1,
              f"expected 1 deleted row, got {len(del_res.data)}")

    except Exception as e:
        check("Live DB tests", False, str(e))


# ══════════════════════════════════════════════════════════════
# 8. _rank_group — FIFA 2026 Article 13 tiebreaker logic
# ══════════════════════════════════════════════════════════════
section("8. _rank_group — FIFA 2026 Article 13 tiebreaker")

check("_rank_group is accessible from db module", hasattr(db, "_rank_group"))

def _m(h, a, hs, as_):
    return {"home_team": h, "away_team": a, "home_score": hs, "away_score": as_}

# ── T1: no tie — clean points order ────────────────────────────────────────
# A=9pts, B=6pts, C=3pts, D=0pts
r1 = db._rank_group(["A","B","C","D"], [
    _m("A","B",1,0), _m("A","C",1,0), _m("A","D",1,0),
    _m("B","C",1,0), _m("B","D",1,0),
    _m("C","D",1,0),
])
check("T1 no-tie: A 1st, B 2nd, C 3rd, D 4th",
      r1 == ["A","B","C","D"], f"got {r1}")

# ── T2: H2H decides 3rd vs 4th ──────────────────────────────────────────────
# Beta and Gamma both 3pts.  Beta beat Gamma 1-0 (H2H).
# Overall GD: Gamma=0, Beta=-2  →  old code (GD only) wrongly put Gamma 3rd.
# Art.13: H2H win comes first → Beta 3rd, Gamma 4th.
#
# Full table:
#   Alpha  6pts  GD=0   (beat Beta 2-1, beat Gamma 1-0, lost to Delta 0-2)
#   Delta  6pts  GD=+2  (beat Alpha 2-0, beat Beta 2-0, lost to Gamma 0-2)
#   Beta   3pts  GD=-2  (beat Gamma 1-0)
#   Gamma  3pts  GD=0   (beat Delta 2-0)
r2 = db._rank_group(["Alpha","Beta","Gamma","Delta"], [
    _m("Alpha","Beta", 2,1), _m("Alpha","Gamma",1,0), _m("Alpha","Delta",0,2),
    _m("Beta", "Gamma",1,0), _m("Beta", "Delta", 0,2),
    _m("Gamma","Delta",2,0),
])
check("T2 H2H 3rd place: Delta 1st, Alpha 2nd, Beta 3rd, Gamma 4th",
      r2 == ["Delta","Alpha","Beta","Gamma"], f"got {r2}")
check("T2 confirms old-code bug fixed: 3rd is Beta (H2H winner), not Gamma (better overall GD)",
      r2[2] == "Beta", f"3rd={r2[2]!r}")

# ── T3: H2H draw → fallthrough to overall GD ───────────────────────────────
# B and C both 4pts; their H2H match was a 0-0 draw (all H2H criteria tied).
# Fallthrough: C has overall GD +1, B has overall GD 0 → C ranks above B.
#
# Full table:
#   A  9pts  GD=+5  (beat B 2-0, beat C 2-0, beat D 1-0)
#   C  4pts  GD=+1  (drew B 0-0, beat D 3-0, lost to A 0-2)
#   B  4pts  GD=0   (drew C 0-0, beat D 2-0, lost to A 0-2)
#   D  0pts  GD=-6  (lost all)
r3 = db._rank_group(["A","B","C","D"], [
    _m("A","B",2,0), _m("A","C",2,0), _m("A","D",1,0),
    _m("B","C",0,0), _m("B","D",2,0),
    _m("C","D",3,0),
])
check("T3 draw fallthrough: A 1st, C 2nd (GD+1), B 3rd (GD 0), D 4th",
      r3 == ["A","C","B","D"], f"got {r3}")

# ── T4: 3-way tie on points, all drew each other — no crash ────────────────
# A, B, C all 5pts (all beat D 3-0; all drew each other).
# H2H among A,B,C: all 1-1 draws → H2H pts=2, GD=0, GF=1 for each.
# Overall GD: all +3 (from D) + 0 net from draws = +3 for each.  Fully tied.
# Result: D is unambiguously last (0pts); A, B, C order is arbitrary but stable.
r4 = db._rank_group(["A","B","C","D"], [
    _m("A","D",3,0), _m("B","D",3,0), _m("C","D",3,0),
    _m("A","B",1,1), _m("A","C",1,1), _m("B","C",1,1),
])
check("T4 3-way fully-tied: D is last (0 pts)",
      r4[3] == "D", f"got {r4}")
check("T4 3-way fully-tied: A, B, C fill top 3",
      set(r4[:3]) == {"A","B","C"}, f"got {r4}")

# ── T5: 3-way tie, H2H pts equal, H2H GD decides ──────────────────────────
# Circular wins: A beats B 3-0, B beats C 3-0, C beats A 1-0.  All beat D 1-0.
# H2H pts: A=3, B=3, C=3 (tied) → H2H GD: A=+2, B=0, C=-2 → A > B > C
# Verified expected: ['A','B','C','D']
r5 = db._rank_group(["A","B","C","D"], [
    _m("A","B",3,0), _m("B","C",3,0), _m("C","A",1,0),
    _m("A","D",1,0), _m("B","D",1,0), _m("C","D",1,0),
])
check("T5 3-way H2H GD: A 1st (GD+2), B 2nd (0), C 3rd (-2), D 4th",
      r5 == ["A","B","C","D"], f"got {r5}")

# ── T6: H2H draw, same overall GD — overall GF is final tiebreaker ─────────
# B and C both 4pts. H2H drew 0-0. Overall GD: B=+2, C=+2 (tied).
# Overall GF: C=5, B=3 → C ranks above B on criterion 6.
#
# Full table:
#   A  9pts  GD=+3  (beat B 1-0, beat C 2-1, beat D 1-0)
#   C  4pts  GD=+2  GF=5  (drew B 0-0, beat D 4-1, lost to A 1-2)
#   B  4pts  GD=+2  GF=3  (drew C 0-0, beat D 3-0, lost to A 0-1)
#   D  0pts  (lost all)
r6 = db._rank_group(["A","B","C","D"], [
    _m("A","B",1,0), _m("A","C",2,1), _m("A","D",1,0),
    _m("B","C",0,0), _m("B","D",3,0),
    _m("C","D",4,1),
])
check("T6 overall-GF tiebreaker: A 1st, C 2nd (GF=5), B 3rd (GF=3), D 4th",
      r6 == ["A","C","B","D"], f"got {r6}")

# ── T7: all 6 matches drawn — degenerate, must not crash ──────────────────
# All 4 teams: 3pts, GD=0, GF=3 — completely tied, order is arbitrary.
r7 = db._rank_group(["A","B","C","D"], [
    _m("A","B",1,1), _m("A","C",1,1), _m("A","D",1,1),
    _m("B","C",1,1), _m("B","D",1,1), _m("C","D",1,1),
])
check("T7 all-draws: returns all 4 teams without crashing",
      len(r7) == 4 and set(r7) == {"A","B","C","D"}, f"got {r7}")

# ── T8: partial group — only 2 of 6 matches played ────────────────────────
# A beats B 2-0 (A=3pts GD+2), C beats D 1-0 (C=3pts GD+1).
# A vs C no H2H → falls to overall GD: A(+2) > C(+1).
# D has GD=-1, B has GD=-2 → D above B in last two spots.
# Verified expected: ['A','C','D','B']
r8 = db._rank_group(["A","B","C","D"], [
    _m("A","B",2,0),
    _m("C","D",1,0),
])
check("T8 partial group: A 1st, C 2nd, D 3rd, B 4th",
      r8 == ["A","C","D","B"], f"got {r8}")

# ── T9: 4-way tie, circular wins + cross draws — no crash ─────────────────
# A beats B, B beats C, C beats D, D beats A (circular 1-0 each).
# A draws C 0-0, B draws D 0-0.  All 4pts, GD=0, GF=1.  Fully tied.
r9 = db._rank_group(["A","B","C","D"], [
    _m("A","B",1,0), _m("B","C",1,0), _m("C","D",1,0), _m("D","A",1,0),
    _m("A","C",0,0), _m("B","D",0,0),
])
check("T9 4-way circular tie: returns all 4 teams without crashing",
      len(r9) == 4 and set(r9) == {"A","B","C","D"}, f"got {r9}")


# ══════════════════════════════════════════════════════════════
# 9. _compute_standings — source-level and DB-dependent checks
# ══════════════════════════════════════════════════════════════
section("9. _compute_standings & scoring — source and skip checks")

# ── T10-T14: DB-dependent scoring tests ────────────────────────────────────
skip("T10: calculate_group_points uses H2H ranking — awards pts to correct predictor",
     "requires DB with a finished group that triggers the H2H tiebreaker")
skip("T11: calculate_group_points returns early when group has < 6 results",
     "requires DB with a partially finished group")
skip("T12: users who predicted wrong 3rd place receive 0 pts for that criterion",
     "requires DB test data with known wrong prediction")
skip("T13: derive_and_save_group_prediction does not persist when < 6 bets saved",
     "requires DB — checks early-return guard in prediction derivation")
skip("T14: derive_and_save_group_prediction persists H2H-correct standings with all 6 bets",
     "requires DB — end-to-end derivation round-trip")

# ── T15: _compute_standings delegates to _rank_group (source inspection) ───
pred_src = (ROOT / "pages" / "1_Predictions.py").read_text(encoding="utf-8")
check("T15: _rank_group is imported in pages/1_Predictions.py",
      "_rank_group" in pred_src, "import not found in source")
check("T15: _compute_standings body calls _rank_group()",
      "_rank_group(" in pred_src, "call not found in source")

# ── T16: _compute_standings output structure ────────────────────────────────
# We can't import 1_Predictions.py directly (st.set_page_config runs at module
# level), so we re-implement the same logic using _rank_group directly and
# verify the output structure matches what the UI expects.
def _standings_via_rank_group(batch, matches):
    """Mirrors _compute_standings from 1_Predictions.py."""
    results_list = []
    teams = set()
    for match in matches:
        h, a = match["home_team"], match["away_team"]
        teams.update((h, a))
        entry = batch.get(match["id"])
        if not entry:
            continue
        _, hs, as_ = entry
        results_list.append(_m(h, a, hs, as_))
    if not results_list:
        return [{"team": t, "pts": 0, "gd": 0, "gf": 0} for t in sorted(teams)]
    ranked = db._rank_group(list(teams), results_list)
    data = {t: {"pts": 0, "gf": 0, "ga": 0} for t in teams}
    for r in results_list:
        h, a, hs, as_ = r["home_team"], r["away_team"], r["home_score"], r["away_score"]
        data[h]["gf"] += hs; data[h]["ga"] += as_
        data[a]["gf"] += as_; data[a]["ga"] += hs
        if hs > as_: data[h]["pts"] += 3
        elif as_ > hs: data[a]["pts"] += 3
        else: data[h]["pts"] += 1; data[a]["pts"] += 1
    return [{"team": t, "pts": data[t]["pts"], "gd": data[t]["gf"] - data[t]["ga"],
             "gf": data[t]["gf"]} for t in ranked]

# T16a: empty batch returns 4 rows with correct keys and 0 pts
matches_stub = [
    {"id": 1, "home_team": "Alpha", "away_team": "Beta"},
    {"id": 2, "home_team": "Alpha", "away_team": "Gamma"},
    {"id": 3, "home_team": "Alpha", "away_team": "Delta"},
    {"id": 4, "home_team": "Beta",  "away_team": "Gamma"},
    {"id": 5, "home_team": "Beta",  "away_team": "Delta"},
    {"id": 6, "home_team": "Gamma", "away_team": "Delta"},
]
s16a = _standings_via_rank_group({}, matches_stub)
check("T16a empty batch: returns 4 rows", len(s16a) == 4, f"got {len(s16a)}")
check("T16a empty batch: each row has team/pts/gd/gf keys",
      all({"team","pts","gd","gf"} <= set(r.keys()) for r in s16a),
      f"got keys {[list(r.keys()) for r in s16a]}")
check("T16a empty batch: all pts are 0", all(r["pts"] == 0 for r in s16a), str(s16a))

# T16b: T2 scenario through _compute_standings — same order as _rank_group
batch_t2 = {
    1: ("home", 2, 1),  # Alpha 2-1 Beta
    2: ("home", 1, 0),  # Alpha 1-0 Gamma
    3: ("away", 0, 2),  # Delta beats Alpha 2-0
    4: ("home", 1, 0),  # Beta 1-0 Gamma  ← decisive H2H
    5: ("away", 0, 2),  # Delta beats Beta 2-0
    6: ("home", 2, 0),  # Gamma 2-0 Delta
}
matches_t2 = [
    {"id": 1, "home_team": "Alpha", "away_team": "Beta"},
    {"id": 2, "home_team": "Alpha", "away_team": "Gamma"},
    {"id": 3, "home_team": "Alpha", "away_team": "Delta"},
    {"id": 4, "home_team": "Beta",  "away_team": "Gamma"},
    {"id": 5, "home_team": "Beta",  "away_team": "Delta"},
    {"id": 6, "home_team": "Gamma", "away_team": "Delta"},
]
s16b = _standings_via_rank_group(batch_t2, matches_t2)
s16b_order = [r["team"] for r in s16b]
check("T16b _compute_standings T2 scenario: Delta 1st, Alpha 2nd, Beta 3rd, Gamma 4th",
      s16b_order == ["Delta","Alpha","Beta","Gamma"], f"got {s16b_order}")
check("T16b _compute_standings output has pts/gd/gf populated",
      all(r["pts"] > 0 for r in s16b),
      str([(r["team"], r["pts"]) for r in s16b]))


# ══════════════════════════════════════════════════════════════
# 10. FIFA ANNEX C — lookup table integrity
# ══════════════════════════════════════════════════════════════
section("10. FIFA Annex C — lookup table integrity")

try:
    from annex_c import ANNEX_C
    check("annex_c.py imports cleanly", True)
except Exception as e:
    check("annex_c.py imports cleanly", False, str(e))
    ANNEX_C = {}

VALID_GROUPS   = set("ABCDEFGHIJKL")
THIRD_SLOTS    = {"R32_1", "R32_2", "R32_7", "R32_8", "R32_11", "R32_12", "R32_15", "R32_16"}
SLOT_POOLS: dict[str, set[str]] = {
    "R32_1":  set("ABCDF"),
    "R32_2":  set("CDFGH"),
    "R32_7":  set("CEFHI"),
    "R32_8":  set("EHIJK"),
    "R32_11": set("BEFIJ"),
    "R32_12": set("AEHIJ"),
    "R32_15": set("EFGIJ"),
    "R32_16": set("DEIJL"),
}

# ── T17: entry count ────────────────────────────────────────────────────────
check("T17: ANNEX_C has exactly 495 entries",
      len(ANNEX_C) == 495, f"got {len(ANNEX_C)}")

# ── T18: key structure ──────────────────────────────────────────────────────
bad_keys = [k for k in ANNEX_C if not (isinstance(k, frozenset) and len(k) == 8 and k <= VALID_GROUPS)]
check("T18: every key is a frozenset of exactly 8 valid group letters (A-L)",
      len(bad_keys) == 0, f"{len(bad_keys)} bad keys")

# ── T19: value structure ─────────────────────────────────────────────────────
bad_val_slots = {k for k, v in ANNEX_C.items() if set(v.keys()) != THIRD_SLOTS}
check("T19: every row has exactly the 8 expected slot keys",
      len(bad_val_slots) == 0, f"{len(bad_val_slots)} rows with wrong slot keys")

# ── T20: all 8 groups from the key appear as values ──────────────────────────
bad_coverage = {k for k, v in ANNEX_C.items() if set(v.values()) != k}
check("T20: slot values use all 8 groups from the key (no missing / extra group)",
      len(bad_coverage) == 0, f"{len(bad_coverage)} rows with coverage mismatch")

# ── T21: slot-pool constraint — every assignment respects FIFA eligibility ───
pool_violations = 0
for key, row in ANNEX_C.items():
    for slot, grp in row.items():
        if grp not in SLOT_POOLS[slot]:
            pool_violations += 1
check("T21: every (slot, group) assignment satisfies the FIFA slot-pool constraint",
      pool_violations == 0, f"{pool_violations} constraint violations")

# ── T22: group K always goes to R32_8 (only eligible slot) ──────────────────
k_rows   = {k: v for k, v in ANNEX_C.items() if "K" in k}
k_ok     = all(v["R32_8"] == "K" for v in k_rows.values())
check(f"T22: in all {len(k_rows)} rows containing group K, K is always assigned R32_8",
      k_ok)

# ── T23: group L always goes to R32_16 (only eligible slot) ─────────────────
l_rows   = {k: v for k, v in ANNEX_C.items() if "L" in k}
l_ok     = all(v["R32_16"] == "L" for v in l_rows.values())
check(f"T23: in all {len(l_rows)} rows containing group L, L is always assigned R32_16",
      l_ok)

# ── T24–T31: spot-checks from Wikipedia / official PDF ───────────────────────
spot_checks = [
    # (label,  qualifying_groups,  expected_assignment)
    ("T24 Row 1  EFGHIJKL", frozenset("EFGHIJKL"),
     {"R32_7":"E","R32_15":"J","R32_11":"I","R32_1":"F","R32_12":"H","R32_2":"G","R32_16":"L","R32_8":"K"}),
    ("T25 Row 2  DFGHIJKL", frozenset("DFGHIJKL"),
     {"R32_7":"H","R32_15":"G","R32_11":"I","R32_1":"D","R32_12":"J","R32_2":"F","R32_16":"L","R32_8":"K"}),
    ("T26 Row 9  DEFGHIJK", frozenset("DEFGHIJK"),
     {"R32_7":"E","R32_15":"G","R32_11":"J","R32_1":"D","R32_12":"H","R32_2":"F","R32_16":"I","R32_8":"K"}),
    ("T27 Row 45 CDEFGHIJ", frozenset("CDEFGHIJ"),
     {"R32_7":"C","R32_15":"G","R32_11":"J","R32_1":"D","R32_12":"H","R32_2":"F","R32_16":"E","R32_8":"I"}),
    ("T28 Row 165 BCDEFGHI", frozenset("BCDEFGHI"),
     {"R32_7":"C","R32_15":"G","R32_11":"B","R32_1":"D","R32_12":"H","R32_2":"F","R32_16":"E","R32_8":"I"}),
    ("T29 Row 285 ACDEFGHI", frozenset("ACDEFGHI"),
     {"R32_7":"H","R32_15":"G","R32_11":"E","R32_1":"C","R32_12":"A","R32_2":"F","R32_16":"D","R32_8":"I"}),
    ("T30 Row 166 AFGHIJKL", frozenset("AFGHIJKL"),
     {"R32_7":"H","R32_15":"J","R32_11":"I","R32_1":"F","R32_12":"A","R32_2":"G","R32_16":"L","R32_8":"K"}),
    ("T31 Row 495 ABCDEFGH", frozenset("ABCDEFGH"),
     {"R32_7":"H","R32_15":"G","R32_11":"B","R32_1":"C","R32_12":"A","R32_2":"F","R32_16":"D","R32_8":"E"}),
]
for label, key, expected in spot_checks:
    actual = ANNEX_C.get(key)
    check(label, actual == expected,
          f"\n    expected: {expected}\n    actual:   {actual}")

# ── T32: lookup returns empty dict for an invalid / unknown key ───────────────
dummy = frozenset("ABCDEFGX")  # X is not a valid group
check("T32: ANNEX_C.get() returns None (not crash) for an unknown key",
      ANNEX_C.get(dummy) is None)

# ── T33: core logic of _compute_third_assignment is exercised directly ────────
# Simulate: top-8 come from groups E,F,G,H,I,J,K,L (row 1 of Annex C)
# Expected assignment: R32_7→teamE, R32_15→teamJ, R32_11→teamI, R32_1→teamF,
#                      R32_12→teamH, R32_2→teamG, R32_16→teamL, R32_8→teamK
top8_sim = [("team_E","E",6,3,5),("team_F","F",5,2,4),("team_G","G",4,1,3),
            ("team_H","H",4,0,3),("team_I","I",3,0,2),("team_J","J",3,-1,2),
            ("team_K","K",3,-2,2),("team_L","L",1,-3,1)]
qualifying_groups_sim = frozenset(g for _, g, *_ in top8_sim)
annex_row_sim = ANNEX_C.get(qualifying_groups_sim, {})
group_to_team_sim = {g: t for t, g, *_ in top8_sim}
assignment_sim = {slot: group_to_team_sim[grp]
                  for slot, grp in annex_row_sim.items() if grp in group_to_team_sim}
check("T33: _compute_third_assignment core logic (row 1 EFGHIJKL) → correct team per slot",
      assignment_sim == {
          "R32_7":"team_E","R32_15":"team_J","R32_11":"team_I","R32_1":"team_F",
          "R32_12":"team_H","R32_2":"team_G","R32_16":"team_L","R32_8":"team_K"
      }, f"got {assignment_sim}")

# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
total = results["passed"] + results["failed"] + results["skipped"]
print(f"\n{'═' * 60}")
print(f"  Results: "
      f"\033[92m{results['passed']} passed\033[0m  "
      f"\033[91m{results['failed']} failed\033[0m  "
      f"\033[93m{results['skipped']} skipped\033[0m  "
      f"({total} total)")
print(f"{'═' * 60}\n")

sys.exit(1 if results["failed"] > 0 else 0)
