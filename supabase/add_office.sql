-- ============================================================
-- MIGRATION: Add office column to users
-- Run this once in the Supabase SQL Editor
-- ============================================================

-- 1. Add the office column (nullable so existing rows are unaffected)
ALTER TABLE users ADD COLUMN IF NOT EXISTS office TEXT;

-- 2. Recreate the leaderboard view to expose the office column
--    (DROP + CREATE is needed because Supabase doesn't support
--     ALTER VIEW for column additions)
DROP VIEW IF EXISTS leaderboard CASCADE;

CREATE VIEW leaderboard AS
WITH
  bet_pts AS (
      SELECT user_id, COALESCE(SUM(points_earned), 0) AS total
      FROM bets
      GROUP BY user_id
  ),
  group_pts AS (
      SELECT user_id, COALESCE(SUM(points_earned), 0) AS total
      FROM group_predictions
      GROUP BY user_id
  ),
  ko_pts AS (
      SELECT user_id, COALESCE(SUM(points_earned), 0) AS total
      FROM knockout_predictions
      GROUP BY user_id
  )
SELECT
    u.id,
    u.name,
    u.office,
    COALESCE(b.total,  0) AS group_stage_points,
    COALESCE(gp.total, 0) AS group_prediction_points,
    COALESCE(kp.total, 0) AS knockout_points,
    COALESCE(b.total,  0)
        + COALESCE(gp.total, 0)
        + COALESCE(kp.total, 0) AS total_points
FROM users u
LEFT JOIN bet_pts   b  ON b.user_id  = u.id
LEFT JOIN group_pts gp ON gp.user_id = u.id
LEFT JOIN ko_pts    kp ON kp.user_id = u.id
ORDER BY total_points DESC;

-- 3. RLS note: the app uses the service-role key so RLS is bypassed.
--    If you ever expose a user-scoped key, add an UPDATE policy like:
--    CREATE POLICY "Users update own office"
--        ON users FOR UPDATE
--        USING (auth.uid() = id)
--        WITH CHECK (auth.uid() = id);
