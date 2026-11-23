-- 02_explore.sql
-- First exploratory queries. Run with:  python src/run_sql.py sql/02_explore.sql
-- Each query starts with a "-- Q" comment line that is used as its title.
-- Note: one row in ladder_entries = one player on one race.

-- Q1: How many ladder entries do we have per region?
SELECT
    CASE s.region_id WHEN 1 THEN 'US' WHEN 2 THEN 'EU' WHEN 3 THEN 'KR' END AS region,
    COUNT(*) AS entries,
    COUNT(DISTINCT e.player_key) AS unique_players,
    ROUND(AVG(e.mmr)) AS avg_mmr,
    MIN(e.mmr) AS min_mmr,
    MAX(e.mmr) AS max_mmr
FROM ladder_entries e
JOIN snapshots s ON s.snapshot_id = e.snapshot_id
GROUP BY s.region_id
ORDER BY s.region_id;

-- Q2: Race distribution by region (share of each region's entries, using a window function)
SELECT
    CASE s.region_id WHEN 1 THEN 'US' WHEN 2 THEN 'EU' WHEN 3 THEN 'KR' END AS region,
    e.race,
    COUNT(*) AS entries,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY s.region_id), 1) AS pct_of_region
FROM ladder_entries e
JOIN snapshots s ON s.snapshot_id = e.snapshot_id
GROUP BY s.region_id, e.race
ORDER BY s.region_id, entries DESC;

-- Q3: Win rate and average MMR by race (all regions combined)
SELECT
    e.race,
    COUNT(*) AS entries,
    SUM(e.wins) AS total_wins,
    SUM(e.losses) AS total_losses,
    ROUND(100.0 * SUM(e.wins) / (SUM(e.wins) + SUM(e.losses)), 2) AS win_rate_pct,
    ROUND(AVG(e.mmr)) AS avg_mmr
FROM ladder_entries e
GROUP BY e.race
ORDER BY win_rate_pct DESC;

-- Q4: Top 10 entries by MMR within each region, only entries with 20+ games (RANK window function)
WITH ranked AS (
    SELECT
        CASE s.region_id WHEN 1 THEN 'US' WHEN 2 THEN 'EU' WHEN 3 THEN 'KR' END AS region,
        e.race,
        e.mmr,
        e.wins,
        e.losses,
        RANK() OVER (PARTITION BY s.region_id ORDER BY e.mmr DESC) AS mmr_rank
    FROM ladder_entries e
    JOIN snapshots s ON s.snapshot_id = e.snapshot_id
    WHERE e.wins + e.losses >= 20
)
SELECT * FROM ranked WHERE mmr_rank <= 10 ORDER BY region, mmr_rank;

-- Q5: How many players play more than one race?
WITH per_player AS (
    SELECT e.player_key, COUNT(*) AS races_played
    FROM ladder_entries e
    GROUP BY e.player_key
)
SELECT races_played, COUNT(*) AS players
FROM per_player
GROUP BY races_played
ORDER BY races_played;
