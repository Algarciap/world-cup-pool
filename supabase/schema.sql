-- ============================================================
-- WORLD CUP POOL 2026 — DATABASE SCHEMA
-- Run this in the Supabase SQL Editor (https://supabase.com/dashboard)
-- ============================================================

-- Drop existing objects to allow clean re-runs
DROP VIEW  IF EXISTS leaderboard               CASCADE;
DROP TABLE IF EXISTS tournament_predictions    CASCADE;
DROP TABLE IF EXISTS knockout_predictions      CASCADE;
DROP TABLE IF EXISTS group_predictions         CASCADE;
DROP TABLE IF EXISTS bets                      CASCADE;
DROP TABLE IF EXISTS matches                   CASCADE;
DROP TABLE IF EXISTS teams                     CASCADE;
DROP TABLE IF EXISTS users                     CASCADE;

-- Enable UUID support
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ============================================================
-- USERS
-- Stores all participants and admins
-- ============================================================
CREATE TABLE users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    email       TEXT        UNIQUE NOT NULL,
    is_admin    BOOLEAN     DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT now()
);


-- ============================================================
-- TEAMS
-- All 48 qualified teams with their group assignment
-- ============================================================
CREATE TABLE teams (
    id          SERIAL      PRIMARY KEY,
    name        TEXT        UNIQUE NOT NULL,
    group_name  TEXT        NOT NULL,   -- 'A' through 'L'
    flag_url    TEXT                    -- optional, for UI display
);


-- ============================================================
-- MATCHES
-- All 104 matches: 72 group stage + 32 knockout
-- ============================================================
CREATE TABLE matches (
    id          SERIAL      PRIMARY KEY,
    home_team   TEXT        NOT NULL,
    away_team   TEXT        NOT NULL,
    match_date  TIMESTAMPTZ NOT NULL,
    stage       TEXT        NOT NULL,
        -- 'group' | 'round_of_32' | 'round_of_16' |
        -- 'quarter_final' | 'semi_final' | 'third_place' | 'final'
    group_name  TEXT,
        -- 'A' to 'L' for group stage matches, NULL for knockouts
    slot        TEXT,
        -- NULL for group stage
        -- Knockout slots: 'R32_1'..'R32_16', 'R16_1'..'R16_8',
        --                 'QF_1'..'QF_4', 'SF_1', 'SF_2',
        --                 'THIRD_PLACE', 'FINAL'
    home_score  INT,        -- NULL until match is played
    away_score  INT,        -- NULL until match is played
    status      TEXT        DEFAULT 'upcoming'
        -- 'upcoming' | 'finished'
);


-- ============================================================
-- BETS
-- Group stage predictions: one row per user per match
-- Locked before tournament kickoff, never editable after
-- ============================================================
CREATE TABLE bets (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id             INT         NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    predicted_winner     TEXT        NOT NULL,
        -- 'home' | 'draw' | 'away'
    predicted_home_score INT,        -- optional, awards bonus point if exact
    predicted_away_score INT,        -- optional, awards bonus point if exact
    points_earned        INT,        -- NULL until match result is entered by admin
    created_at           TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, match_id)
);


-- ============================================================
-- GROUP PREDICTIONS
-- Who each participant thinks finishes 1st, 2nd, and 3rd
-- in each of the 12 groups (needed for bracket + 3rd-place slots)
-- ============================================================
CREATE TABLE group_predictions (
    id            UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_name    TEXT    NOT NULL,   -- 'A' through 'L'
    first_place   TEXT    NOT NULL,   -- team name
    second_place  TEXT    NOT NULL,   -- team name
    third_place   TEXT    NOT NULL,   -- team name (required for 3rd-place qualifier logic)
    points_earned INT,                -- awarded after group stage is complete
    created_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, group_name)
);


-- ============================================================
-- KNOCKOUT PREDICTIONS
-- One row per bracket slot per user (15 slots total per user)
-- The slot is auto-filled from their group_predictions when
-- they open the bracket form
-- ============================================================
CREATE TABLE knockout_predictions (
    id               UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot             TEXT    NOT NULL,
        -- Round of 32 : 'R32_1'  to 'R32_16'
        -- Round of 16 : 'R16_1'  to 'R16_8'
        -- Quarter Final: 'QF_1'  to 'QF_4'
        -- Semi Final   : 'SF_1', 'SF_2'
        -- Third place  : 'THIRD_PLACE'
        -- Final        : 'FINAL'
    predicted_winner TEXT    NOT NULL,   -- team name they predict wins this slot
    pred_home_score  INT,               -- optional, for bonus point
    pred_away_score  INT,               -- optional, for bonus point
    points_earned    INT,               -- NULL until that match is played
    created_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, slot)
);


-- ============================================================
-- TOURNAMENT PREDICTIONS
-- Pre-tournament specials: one row per participant
-- ============================================================
CREATE TABLE tournament_predictions (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID    UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    champion    TEXT    NOT NULL,   -- country predicted to win the tournament
    top_scorer  TEXT,               -- player name (optional)
    created_at  TIMESTAMPTZ DEFAULT now()
);


-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Supabase requires this to control who can read/write what
-- ============================================================

ALTER TABLE users                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches               ENABLE ROW LEVEL SECURITY;
ALTER TABLE bets                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE group_predictions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE knockout_predictions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE tournament_predictions ENABLE ROW LEVEL SECURITY;

-- Everyone can read teams and matches (public fixture list)
CREATE POLICY "Public read teams"   ON teams   FOR SELECT USING (true);
CREATE POLICY "Public read matches" ON matches FOR SELECT USING (true);

-- Users can read all other users' names (for leaderboard)
CREATE POLICY "Public read users"   ON users   FOR SELECT USING (true);

-- Users can only insert/update their own rows
CREATE POLICY "Users insert own bets"
    ON bets FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users read own bets"
    ON bets FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users insert own group predictions"
    ON group_predictions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users read own group predictions"
    ON group_predictions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users insert own knockout predictions"
    ON knockout_predictions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users read own knockout predictions"
    ON knockout_predictions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users insert own tournament predictions"
    ON tournament_predictions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users read own tournament predictions"
    ON tournament_predictions FOR SELECT
    USING (auth.uid() = user_id);

-- Leaderboard: everyone can read points earned (but not the predictions themselves)
CREATE POLICY "Public read bets points"
    ON bets FOR SELECT
    USING (true);

CREATE POLICY "Public read knockout points"
    ON knockout_predictions FOR SELECT
    USING (true);

-- Admin: full access (admins have is_admin = true in users table)
-- These policies are applied via a Supabase service role key in the backend,
-- not as individual row policies. Use the service_role key in your admin panel only.


-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- Leaderboard: total points per user across all prediction tables
CREATE VIEW leaderboard AS
SELECT
    u.id,
    u.name,
    COALESCE(SUM(b.points_earned),  0)  AS group_stage_points,
    COALESCE(SUM(gp.points_earned), 0)  AS group_prediction_points,
    COALESCE(SUM(kp.points_earned), 0)  AS knockout_points,
    COALESCE(SUM(b.points_earned),  0)
        + COALESCE(SUM(gp.points_earned), 0)
        + COALESCE(SUM(kp.points_earned), 0) AS total_points
FROM users u
LEFT JOIN bets b                 ON b.user_id  = u.id
LEFT JOIN group_predictions gp   ON gp.user_id = u.id
LEFT JOIN knockout_predictions kp ON kp.user_id = u.id
GROUP BY u.id, u.name
ORDER BY total_points DESC;
