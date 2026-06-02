"""
Smoke test for THIRD_PLACE loser derivation logic.
No DB, no Streamlit required — run with: python scripts/test_third_place.py
"""
import sys
sys.path.insert(0, ".")
from db import flag_img, TEAM_CODES

# ── Replicate the exact logic from pages/1_Predictions.py ─────────────────────

def _sf_loser_teams(saved_ko_preds: dict) -> tuple:
    sf1_a = saved_ko_preds.get("QF_1", {}).get("predicted_winner")
    sf1_b = saved_ko_preds.get("QF_2", {}).get("predicted_winner")
    sf1_w = saved_ko_preds.get("SF_1", {}).get("predicted_winner")
    loser1 = (sf1_b if sf1_w == sf1_a else sf1_a) if (sf1_a and sf1_b and sf1_w in (sf1_a, sf1_b)) else None

    sf2_a = saved_ko_preds.get("QF_3", {}).get("predicted_winner")
    sf2_b = saved_ko_preds.get("QF_4", {}).get("predicted_winner")
    sf2_w = saved_ko_preds.get("SF_2", {}).get("predicted_winner")
    loser2 = (sf2_b if sf2_w == sf2_a else sf2_a) if (sf2_a and sf2_b and sf2_w in (sf2_a, sf2_b)) else None

    return loser1, loser2


def run_test(name: str, preds: dict, expected: tuple):
    result = _sf_loser_teams(preds)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    print(f"{status}  {name}")
    if result != expected:
        print(f"       expected: {expected}")
        print(f"       got:      {result}")


# ── Test cases ─────────────────────────────────────────────────────────────────

# Case 1: Both SFs fully picked — losers are correctly derived
run_test(
    "Both SFs complete: Brazil beats France, Spain beats Germany",
    {
        "QF_1": {"predicted_winner": "Brazil"},
        "QF_2": {"predicted_winner": "France"},
        "SF_1": {"predicted_winner": "Brazil"},    # loser → France
        "QF_3": {"predicted_winner": "Spain"},
        "QF_4": {"predicted_winner": "Germany"},
        "SF_2": {"predicted_winner": "Germany"},   # loser → Spain
    },
    expected=("France", "Spain"),
)

# Case 2: SF_1 winner is QF_2 winner
run_test(
    "SF_1 winner is QF_2 team (France wins SF_1)",
    {
        "QF_1": {"predicted_winner": "Brazil"},
        "QF_2": {"predicted_winner": "France"},
        "SF_1": {"predicted_winner": "France"},    # loser → Brazil
        "QF_3": {"predicted_winner": "Spain"},
        "QF_4": {"predicted_winner": "Germany"},
        "SF_2": {"predicted_winner": "Spain"},     # loser → Germany
    },
    expected=("Brazil", "Germany"),
)

# Case 3: SF_2 not yet picked — second loser should be None
run_test(
    "SF_2 not picked yet → second loser is None",
    {
        "QF_1": {"predicted_winner": "Brazil"},
        "QF_2": {"predicted_winner": "France"},
        "SF_1": {"predicted_winner": "Brazil"},    # loser → France
        "QF_3": {"predicted_winner": "Spain"},
        "QF_4": {"predicted_winner": "Germany"},
        # SF_2 missing
    },
    expected=("France", None),
)

# Case 4: Nothing picked yet — both None (dropdown shows all teams as fallback)
run_test(
    "Nothing picked yet → both None",
    {},
    expected=(None, None),
)

# Case 5: QF picks missing — can't derive losers even if SF pick exists
run_test(
    "SF_1 picked but QF_1/QF_2 missing → loser1 is None",
    {
        "SF_1": {"predicted_winner": "Brazil"},
        "QF_3": {"predicted_winner": "Spain"},
        "QF_4": {"predicted_winner": "Germany"},
        "SF_2": {"predicted_winner": "Spain"},
    },
    expected=(None, "Germany"),
)

# ── Flag rendering checks ──────────────────────────────────────────────────────
print("\n── Flag rendering ──")

def check_flags(name: str, preds: dict):
    loser1, loser2 = _sf_loser_teams(preds)
    t1 = f"{flag_img(loser1)}<b>{loser1}</b>" if loser1 else "loser of Semi-Final 1"
    t2 = f"{flag_img(loser2)}<b>{loser2}</b>" if loser2 else "loser of Semi-Final 2"
    html = f"{t1} vs {t2}"
    has_flags = 'flagcdn.com' in html
    flag1_ok = loser1 is None or (TEAM_CODES.get(loser1, "") != "")
    flag2_ok = loser2 is None or (TEAM_CODES.get(loser2, "") != "")
    status = "✅ PASS" if flag1_ok and flag2_ok else "❌ FAIL (missing TEAM_CODES entry)"
    print(f"{status}  {name}")
    print(f"         HTML: {html}\n")

check_flags(
    "Both SFs complete: Brazil beats France, Spain beats Germany",
    {
        "QF_1": {"predicted_winner": "Brazil"},
        "QF_2": {"predicted_winner": "France"},
        "SF_1": {"predicted_winner": "Brazil"},
        "QF_3": {"predicted_winner": "Spain"},
        "QF_4": {"predicted_winner": "Germany"},
        "SF_2": {"predicted_winner": "Germany"},
    },
)

check_flags(
    "SF_2 not yet picked → placeholder text for second team",
    {
        "QF_1": {"predicted_winner": "Brazil"},
        "QF_2": {"predicted_winner": "France"},
        "SF_1": {"predicted_winner": "Brazil"},
    },
)
