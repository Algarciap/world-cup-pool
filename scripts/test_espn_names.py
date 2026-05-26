"""Sweep every WC 2026 tournament date and collect ESPN team display names."""
import requests
from datetime import date, timedelta

espn_names = set()
start = date(2026, 6, 11)
end   = date(2026, 7, 20)

d = start
while d <= end:
    ds = d.strftime("%Y%m%d")
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/soccer"
        f"/fifa.world/scoreboard?dates={ds}&limit=50"
    )
    try:
        r = requests.get(url, timeout=10)
        for e in r.json().get("events", []):
            for c in e["competitions"][0].get("competitors", []):
                espn_names.add(c["team"]["displayName"])
    except Exception as ex:
        print(f"  {ds}: {ex}")
    d += timedelta(days=1)

print(f"Total unique ESPN team names found: {len(espn_names)}")
for n in sorted(espn_names):
    print(" ", n)
