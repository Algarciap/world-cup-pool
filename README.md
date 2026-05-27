# World Cup 2026 — Prediction Pool

An internal company-wide prediction pool for the 2026 World Cup, open to all four offices: **Spain, Malta, South Africa, Nigeria, Zambia and UK**. Participants submit score predictions for all group-stage matches and pick knockout-round winners. Points are awarded automatically as results come in, and a live leaderboard tracks the standings — both globally and per office.

Built with Python and Streamlit. No prior web dev experience — shipped with AI as a pair programmer.

---

## Features

- **No-password login** — enter your name and email to join or recover your predictions
- **Office selection** — choose your office (Spain, Malta, South Africa, Nigeria, Zambia or UK) on sign-up; existing users are prompted once on next login
- **Group stage predictions** — enter a scoreline for each of the 72 group matches; group standings (1st / 2nd / 3rd) are derived automatically from your picks
- **Knockout predictions** — pick the winner of every round from R32 through the Final
- **My Summary** — a read-only slip of everything you've predicted
- **Leaderboard** — live points with rank-movement indicators (▲/▼) and office tabs
- **Office Standings** — per-office summary cards (avg score, player count, top scorer) above the leaderboard; dedicated tab per office with its own ranking
- **Everyone's picks** — see all participants' predictions after lock
- **Admin panel** — password-gated; enter results manually or auto-sync from ESPN
- **Prediction lock** — submissions close automatically at kickoff (June 11, 2026, 19:00 UTC)

---

## Scoring System

| Category | Points |
|---|---|
| Correct match result (win / draw) | **3 pts** |
| Exact scoreline bonus | **+2 pts** |
| Correct group 1st place | **+4 pts** |
| Correct group 2nd place | **+3 pts** |
| Correct group 3rd place | **+2 pts** |
| Round of 32 — correct winner | **2 pts** |
| Round of 16 — correct winner | **4 pts** |
| Quarter-Finals — correct winner | **6 pts** |
| Semi-Finals — correct winner | **8 pts** |
| 3rd place match — correct winner | **5 pts** |
| Final — correct winner | **15 pts** |

---

## Tech Stack

- **[Streamlit](https://streamlit.io)** — UI and app server
- **[Supabase](https://supabase.com)** (PostgreSQL) — database, accessed via service-role key
- **ESPN API** — auto-syncing match results
- **Python 3.11+**, pandas, python-dotenv, requests

---

## Project Structure

```
app.py                  # Home page — login, office prompt and welcome screen
db.py                   # Supabase data access layer
ui.py                   # Shared helpers (fonts, session restore)
requirements.txt
pages/
  1_Predictions.py      # Submit group + knockout predictions
  2_My_Summary.py       # Read-only prediction slip
  3_Leaderboard.py      # Live standings — global + per-office tabs
  4_Everyone.py         # All participants' picks
  5_Admin.py            # Admin panel (password-gated)
scripts/
  sync_results.py       # Standalone ESPN sync (for CI / cron)
supabase/
  schema.sql            # Full DB schema — run this first
  seed.sql              # Teams and match fixtures
  fix_rls.sql           # Row-level security policies
  add_office.sql        # Migration: adds office column + rebuilds leaderboard view
```

---

## Local Setup

**Prerequisites:** Python 3.11+, a free [Supabase](https://supabase.com) project.

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure environment variables**

Create a `.env` file in the project root (or set them in your shell):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
ADMIN_PASSWORD=choose-a-password
```

**3. Set up the database**

In the Supabase SQL editor, run in order:

1. `supabase/schema.sql` — creates all tables and the leaderboard view
2. `supabase/seed.sql` — loads the 48 teams and 104 match fixtures
3. `supabase/add_office.sql` — adds the `office` column to `users` and rebuilds the leaderboard view *(skip if setting up fresh — re-run `schema.sql` instead, which already includes office)*

**4. Run the app**

```bash
streamlit run app.py
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | Project URL from Supabase dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | ✅ | Service-role secret key (bypasses RLS) |
| `ADMIN_PASSWORD` | ✅ | Password for the admin panel |

---

## Streamlit Cloud Deployment

1. Push the repo to GitHub
2. Connect it to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add the three secrets above under **Settings → Secrets** in the Streamlit Cloud dashboard (TOML format):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_SERVICE_KEY = "your-service-role-key"
ADMIN_PASSWORD = "your-admin-password"
```

---

## Syncing Results

Results can be synced from ESPN in two ways:

**From the admin panel** — click "Sync results now" on the Admin page.

**From the command line** (or GitHub Actions):

```bash
# env vars must be set
python scripts/sync_results.py
```

The script exits with code `1` if any errors are encountered, making it safe to use in CI pipelines.

---

## Admin Panel

Access at `/5_Admin` (or via the sidebar). Protected by `ADMIN_PASSWORD`.

- **Auto-sync from ESPN** — fetches completed scores and updates the database
- **Manual entry** — enter scorelines for any upcoming match directly
- **Recalculate points** — trigger group-stage and knockout scoring on demand

