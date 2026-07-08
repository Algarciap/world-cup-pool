"""
Standalone script for syncing World Cup results from ESPN.

Designed to run in a GitHub Actions workflow (or any environment where
SUPABASE_URL and SUPABASE_SERVICE_KEY are available as environment variables).

Usage:
    python scripts/sync_results.py
"""

import sys
import os

# Allow importing db.py from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import sync_results_from_espn  # noqa: E402

result = sync_results_from_espn()

print(f"✅ Synced    : {result['synced']}")
print(f"🆕 Discovered: {result.get('discovered', 0)} new fixture(s) added")
print(f"⏭  Skipped  : {result['skipped']} (not yet finished on ESPN)")

if result["errors"]:
    for err in result["errors"]:
        print(f"❌ {err}", file=sys.stderr)
    sys.exit(1)
