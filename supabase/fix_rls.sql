-- ── Users ─────────────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Anyone can register"   ON users;
DROP POLICY IF EXISTS "Users update own row"  ON users;
CREATE POLICY "Anyone can register"   ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Users update own row"  ON users FOR UPDATE USING (true) WITH CHECK (true);

-- ── Bets ──────────────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Users insert own bets"    ON bets;
DROP POLICY IF EXISTS "Users read own bets"      ON bets;
DROP POLICY IF EXISTS "Public read bets points"  ON bets;
CREATE POLICY "Open read bets"   ON bets FOR SELECT USING (true);
CREATE POLICY "Open insert bets" ON bets FOR INSERT WITH CHECK (true);
CREATE POLICY "Open update bets" ON bets FOR UPDATE USING (true) WITH CHECK (true);

-- ── Group predictions ──────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Users insert own group predictions" ON group_predictions;
DROP POLICY IF EXISTS "Users read own group predictions"   ON group_predictions;
CREATE POLICY "Open read group_predictions"   ON group_predictions FOR SELECT USING (true);
CREATE POLICY "Open insert group_predictions" ON group_predictions FOR INSERT WITH CHECK (true);
CREATE POLICY "Open update group_predictions" ON group_predictions FOR UPDATE USING (true) WITH CHECK (true);

-- ── Knockout predictions ───────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Users insert own knockout predictions" ON knockout_predictions;
DROP POLICY IF EXISTS "Users read own knockout predictions"   ON knockout_predictions;
DROP POLICY IF EXISTS "Public read knockout points"          ON knockout_predictions;
CREATE POLICY "Open read knockout_predictions"   ON knockout_predictions FOR SELECT USING (true);
CREATE POLICY "Open insert knockout_predictions" ON knockout_predictions FOR INSERT WITH CHECK (true);
CREATE POLICY "Open update knockout_predictions" ON knockout_predictions FOR UPDATE USING (true) WITH CHECK (true);

-- ── Tournament predictions ─────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Users insert own tournament predictions" ON tournament_predictions;
DROP POLICY IF EXISTS "Users read own tournament predictions"   ON tournament_predictions;
CREATE POLICY "Open read tournament_predictions"   ON tournament_predictions FOR SELECT USING (true);
CREATE POLICY "Open insert tournament_predictions" ON tournament_predictions FOR INSERT WITH CHECK (true);
CREATE POLICY "Open update tournament_predictions" ON tournament_predictions FOR UPDATE USING (true) WITH CHECK (true);
