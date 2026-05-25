-- ============================================================
-- WORLD CUP POOL 2026 — SEED DATA
-- All 48 teams and 72 group stage matches
-- Dates/times stored in UTC
-- Sources: FIFA (fifa.com) and Wikipedia
-- ============================================================

-- ============================================================
-- 48 TEAMS (12 groups of 4)
-- ============================================================
INSERT INTO teams (name, group_name) VALUES
-- Group A
('Mexico',            'A'),
('South Africa',      'A'),
('South Korea',       'A'),
('Czech Republic',    'A'),
-- Group B
('Canada',            'B'),
('Bosnia and Herzegovina', 'B'),
('Qatar',             'B'),
('Switzerland',       'B'),
-- Group C
('Brazil',            'C'),
('Morocco',           'C'),
('Haiti',             'C'),
('Scotland',          'C'),
-- Group D
('United States',     'D'),
('Paraguay',          'D'),
('Australia',         'D'),
('Turkey',            'D'),
-- Group E
('Germany',           'E'),
('Curaçao',           'E'),
('Ivory Coast',       'E'),
('Ecuador',           'E'),
-- Group F
('Netherlands',       'F'),
('Japan',             'F'),
('Sweden',            'F'),
('Tunisia',           'F'),
-- Group G
('Belgium',           'G'),
('Egypt',             'G'),
('Iran',              'G'),
('New Zealand',       'G'),
-- Group H
('Spain',             'H'),
('Cape Verde',        'H'),
('Saudi Arabia',      'H'),
('Uruguay',           'H'),
-- Group I
('France',            'I'),
('Senegal',           'I'),
('Iraq',              'I'),
('Norway',            'I'),
-- Group J
('Argentina',         'J'),
('Algeria',           'J'),
('Austria',           'J'),
('Jordan',            'J'),
-- Group K
('Portugal',          'K'),
('DR Congo',          'K'),
('Uzbekistan',        'K'),
('Colombia',          'K'),
-- Group L
('England',           'L'),
('Croatia',           'L'),
('Ghana',             'L'),
('Panama',            'L');


-- ============================================================
-- 72 GROUP STAGE MATCHES
-- All times in UTC
-- ============================================================
INSERT INTO matches (home_team, away_team, match_date, stage, group_name) VALUES

-- ============================================================
-- GROUP A — Mexico, South Africa, South Korea, Czech Republic
-- ============================================================
('Mexico',         'South Africa',  '2026-06-11 19:00:00+00', 'group', 'A'),
('South Korea',    'Czech Republic', '2026-06-12 02:00:00+00', 'group', 'A'),
('Czech Republic', 'South Africa',  '2026-06-18 16:00:00+00', 'group', 'A'),
('Mexico',         'South Korea',   '2026-06-19 01:00:00+00', 'group', 'A'),
('Czech Republic', 'Mexico',        '2026-06-25 01:00:00+00', 'group', 'A'),
('South Africa',   'South Korea',   '2026-06-25 01:00:00+00', 'group', 'A'),

-- ============================================================
-- GROUP B — Canada, Bosnia and Herzegovina, Qatar, Switzerland
-- ============================================================
('Canada',                  'Bosnia and Herzegovina', '2026-06-12 19:00:00+00', 'group', 'B'),
('Qatar',                   'Switzerland',            '2026-06-13 19:00:00+00', 'group', 'B'),
('Switzerland',             'Bosnia and Herzegovina', '2026-06-18 19:00:00+00', 'group', 'B'),
('Canada',                  'Qatar',                  '2026-06-18 22:00:00+00', 'group', 'B'),
('Switzerland',             'Canada',                 '2026-06-24 19:00:00+00', 'group', 'B'),
('Bosnia and Herzegovina',  'Qatar',                  '2026-06-24 19:00:00+00', 'group', 'B'),

-- ============================================================
-- GROUP C — Brazil, Morocco, Haiti, Scotland
-- ============================================================
('Brazil',   'Morocco',  '2026-06-13 22:00:00+00', 'group', 'C'),
('Haiti',    'Scotland', '2026-06-14 01:00:00+00', 'group', 'C'),
('Scotland', 'Morocco',  '2026-06-19 22:00:00+00', 'group', 'C'),
('Brazil',   'Haiti',    '2026-06-20 00:30:00+00', 'group', 'C'),
('Scotland', 'Brazil',   '2026-06-24 22:00:00+00', 'group', 'C'),
('Morocco',  'Haiti',    '2026-06-24 22:00:00+00', 'group', 'C'),

-- ============================================================
-- GROUP D — United States, Paraguay, Australia, Turkey
-- ============================================================
('United States', 'Paraguay',   '2026-06-13 01:00:00+00', 'group', 'D'),
('Australia',     'Turkey',     '2026-06-14 04:00:00+00', 'group', 'D'),
('United States', 'Australia',  '2026-06-19 19:00:00+00', 'group', 'D'),
('Turkey',        'Paraguay',   '2026-06-20 03:00:00+00', 'group', 'D'),
('Turkey',        'United States', '2026-06-26 02:00:00+00', 'group', 'D'),
('Paraguay',      'Australia',  '2026-06-26 02:00:00+00', 'group', 'D'),

-- ============================================================
-- GROUP E — Germany, Curaçao, Ivory Coast, Ecuador
-- ============================================================
('Germany',     'Curaçao',     '2026-06-14 17:00:00+00', 'group', 'E'),
('Ivory Coast', 'Ecuador',     '2026-06-14 23:00:00+00', 'group', 'E'),
('Germany',     'Ivory Coast', '2026-06-20 20:00:00+00', 'group', 'E'),
('Ecuador',     'Curaçao',     '2026-06-21 00:00:00+00', 'group', 'E'),
('Curaçao',     'Ivory Coast', '2026-06-25 20:00:00+00', 'group', 'E'),
('Ecuador',     'Germany',     '2026-06-25 20:00:00+00', 'group', 'E'),

-- ============================================================
-- GROUP F — Netherlands, Japan, Sweden, Tunisia
-- ============================================================
('Netherlands', 'Japan',       '2026-06-14 20:00:00+00', 'group', 'F'),
('Sweden',      'Tunisia',     '2026-06-15 02:00:00+00', 'group', 'F'),
('Netherlands', 'Sweden',      '2026-06-20 17:00:00+00', 'group', 'F'),
('Tunisia',     'Japan',       '2026-06-21 04:00:00+00', 'group', 'F'),
('Japan',       'Sweden',      '2026-06-25 23:00:00+00', 'group', 'F'),
('Tunisia',     'Netherlands', '2026-06-25 23:00:00+00', 'group', 'F'),

-- ============================================================
-- GROUP G — Belgium, Egypt, Iran, New Zealand
-- ============================================================
('Belgium',     'Egypt',       '2026-06-15 19:00:00+00', 'group', 'G'),
('Iran',        'New Zealand', '2026-06-16 01:00:00+00', 'group', 'G'),
('Belgium',     'Iran',        '2026-06-21 19:00:00+00', 'group', 'G'),
('New Zealand', 'Egypt',       '2026-06-22 01:00:00+00', 'group', 'G'),
('Egypt',       'Iran',        '2026-06-27 03:00:00+00', 'group', 'G'),
('New Zealand', 'Belgium',     '2026-06-27 03:00:00+00', 'group', 'G'),

-- ============================================================
-- GROUP H — Spain, Cape Verde, Saudi Arabia, Uruguay
-- ============================================================
('Spain',         'Cape Verde',   '2026-06-15 16:00:00+00', 'group', 'H'),
('Saudi Arabia',  'Uruguay',      '2026-06-15 22:00:00+00', 'group', 'H'),
('Spain',         'Saudi Arabia', '2026-06-21 16:00:00+00', 'group', 'H'),
('Uruguay',       'Cape Verde',   '2026-06-21 22:00:00+00', 'group', 'H'),
('Cape Verde',    'Saudi Arabia', '2026-06-27 00:00:00+00', 'group', 'H'),
('Uruguay',       'Spain',        '2026-06-27 00:00:00+00', 'group', 'H'),

-- ============================================================
-- GROUP I — France, Senegal, Iraq, Norway
-- ============================================================
('France',  'Senegal', '2026-06-16 19:00:00+00', 'group', 'I'),
('Iraq',    'Norway',  '2026-06-16 22:00:00+00', 'group', 'I'),
('France',  'Iraq',    '2026-06-22 21:00:00+00', 'group', 'I'),
('Norway',  'Senegal', '2026-06-23 00:00:00+00', 'group', 'I'),
('Norway',  'France',  '2026-06-26 19:00:00+00', 'group', 'I'),
('Senegal', 'Iraq',    '2026-06-26 19:00:00+00', 'group', 'I'),

-- ============================================================
-- GROUP J — Argentina, Algeria, Austria, Jordan
-- ============================================================
('Argentina', 'Algeria', '2026-06-17 01:00:00+00', 'group', 'J'),
('Austria',   'Jordan',  '2026-06-17 04:00:00+00', 'group', 'J'),
('Argentina', 'Austria', '2026-06-22 17:00:00+00', 'group', 'J'),
('Jordan',    'Algeria', '2026-06-23 03:00:00+00', 'group', 'J'),
('Algeria',   'Austria', '2026-06-28 02:00:00+00', 'group', 'J'),
('Jordan',    'Argentina', '2026-06-28 02:00:00+00', 'group', 'J'),

-- ============================================================
-- GROUP K — Portugal, DR Congo, Uzbekistan, Colombia
-- ============================================================
('Portugal',   'DR Congo',   '2026-06-17 17:00:00+00', 'group', 'K'),
('Uzbekistan', 'Colombia',   '2026-06-18 02:00:00+00', 'group', 'K'),
('Portugal',   'Uzbekistan', '2026-06-23 17:00:00+00', 'group', 'K'),
('Colombia',   'DR Congo',   '2026-06-24 02:00:00+00', 'group', 'K'),
('Colombia',   'Portugal',   '2026-06-27 23:30:00+00', 'group', 'K'),
('DR Congo',   'Uzbekistan', '2026-06-27 23:30:00+00', 'group', 'K'),

-- ============================================================
-- GROUP L — England, Croatia, Ghana, Panama
-- ============================================================
('England', 'Croatia', '2026-06-17 20:00:00+00', 'group', 'L'),
('Ghana',   'Panama',  '2026-06-17 23:00:00+00', 'group', 'L'),
('England', 'Ghana',   '2026-06-23 20:00:00+00', 'group', 'L'),
('Panama',  'Croatia', '2026-06-23 23:00:00+00', 'group', 'L'),
('Panama',  'England', '2026-06-27 21:00:00+00', 'group', 'L'),
('Croatia', 'Ghana',   '2026-06-27 21:00:00+00', 'group', 'L');
