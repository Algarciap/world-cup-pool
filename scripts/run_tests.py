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
