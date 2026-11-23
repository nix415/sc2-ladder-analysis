"""Export an anonymized, analysis-ready CSV for Tableau.

Run from the project root:
    python src/export_for_tableau.py

Creates data/processed/ladder_entries.csv. Player names and clan tags are NOT included;
players are identified only by a short hashed ID (safe for Tableau Public).
"""

import hashlib
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "sc2.db"
OUT_DIR = PROJECT_ROOT / "data" / "processed"

MIN_GAMES = 20  # entries with fewer games have unreliable MMR / win rate

QUERY = """
SELECT
    s.pulled_at,
    CASE s.region_id WHEN 1 THEN 'US' WHEN 2 THEN 'EU' WHEN 3 THEN 'KR' END AS region,
    s.league,
    e.player_key,
    e.race,
    e.mmr,
    e.points,
    e.wins,
    e.losses,
    e.wins + e.losses AS games,
    ROUND(100.0 * e.wins / NULLIF(e.wins + e.losses, 0), 1) AS win_rate_pct,
    CASE WHEN e.wins + e.losses >= ? THEN 1 ELSE 0 END AS enough_games,
    COUNT(*) OVER (PARTITION BY e.snapshot_id, e.player_key) AS races_played,
    RANK() OVER (PARTITION BY e.snapshot_id ORDER BY e.mmr DESC) AS mmr_rank_in_region
FROM ladder_entries e
JOIN snapshots s ON s.snapshot_id = e.snapshot_id
ORDER BY s.region_id, e.mmr DESC
"""


def main() -> None:
    if not DB_PATH.exists():
        print("No database found. Run: python src/load_to_db.py")
        return

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(QUERY, conn, params=(MIN_GAMES,))
    conn.close()

    # Replace the real player key with a short hash, then drop the key.
    df["player_id"] = df["player_key"].apply(lambda k: hashlib.sha256(k.encode()).hexdigest()[:10])
    df = df.drop(columns=["player_key"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "ladder_entries.csv"
    df.to_csv(out_path, index=False)

    print(f"Wrote {len(df)} rows to {out_path}")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
