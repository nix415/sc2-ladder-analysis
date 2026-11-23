-- 01_schema.sql
-- Creates the three tables for the project. Safe to run more than once.
--
-- players         : one row per unique player (who they are)
-- snapshots       : one row per data pull (when we pulled it, from which file)
-- ladder_entries  : one row per player PER RACE per snapshot
--                   (the ladder tracks MMR and wins/losses separately for each race a player uses)

CREATE TABLE IF NOT EXISTS players (
    player_key     TEXT PRIMARY KEY,      -- region_id:realm:profile_id, e.g. '1:1:2150678'
    region_id      INTEGER NOT NULL,      -- 1 = US, 2 = EU, 3 = KR
    realm          INTEGER NOT NULL,
    profile_id     TEXT NOT NULL,
    display_name   TEXT,                  -- keep private: do NOT export this for Tableau Public
    clan_tag       TEXT
);

CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    pulled_at      TEXT NOT NULL,         -- UTC time of the pull, e.g. '2026-11-20T23:33:38Z'
    region_id      INTEGER NOT NULL,
    league         TEXT NOT NULL,         -- 'grandmaster' for now; other leagues later
    source_file    TEXT NOT NULL UNIQUE   -- prevents loading the same file twice
);

CREATE TABLE IF NOT EXISTS ladder_entries (
    entry_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id     INTEGER NOT NULL REFERENCES snapshots(snapshot_id),
    player_key      TEXT NOT NULL REFERENCES players(player_key),
    race            TEXT NOT NULL,        -- protoss / zerg / terran / random / unknown (missing in API data)
    mmr             INTEGER,
    points          INTEGER,
    wins            INTEGER,
    losses          INTEGER,
    previous_rank   INTEGER,
    join_timestamp  INTEGER,              -- Unix time (seconds) the player joined this ladder
    UNIQUE (snapshot_id, player_key, race)
);

CREATE INDEX IF NOT EXISTS idx_entries_snapshot ON ladder_entries(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_entries_player   ON ladder_entries(player_key);
