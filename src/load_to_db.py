"""Load the raw ladder JSON files in data/raw/ into a SQLite database.

Run from the project root:
    python src/load_to_db.py

Safe to run repeatedly: files that were already loaded are skipped.
"""

import json
import re
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "data" / "sc2.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "01_schema.sql"

REGION_IDS = {"us": 1, "eu": 2, "kr": 3}

# Matches names like grandmaster_us_20261120T233338Z.json
FILENAME_PATTERN = re.compile(r"^(?P<league>[a-z]+)_(?P<region>[a-z]+)_(?P<stamp>\d{8}T\d{6}Z)\.json$")


def stamp_to_iso(stamp: str) -> str:
    """'20261120T233338Z' -> '2026-11-20T23:33:38Z'"""
    return f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}Z"


def load_file(conn: sqlite3.Connection, path: Path) -> str:
    match = FILENAME_PATTERN.match(path.name)
    if not match:
        return f"skipped (unrecognized name): {path.name}"

    region_name = match.group("region")
    if region_name not in REGION_IDS:
        return f"skipped (unknown region): {path.name}"

    already = conn.execute("SELECT 1 FROM snapshots WHERE source_file = ?", (path.name,)).fetchone()
    if already:
        return f"skipped (already loaded): {path.name}"

    data = json.loads(path.read_text(encoding="utf-8"))
    teams = data.get("ladderTeams", [])

    cur = conn.execute(
        "INSERT INTO snapshots (pulled_at, region_id, league, source_file) VALUES (?, ?, ?, ?)",
        (stamp_to_iso(match.group("stamp")), REGION_IDS[region_name], match.group("league"), path.name),
    )
    snapshot_id = cur.lastrowid

    loaded = 0
    skipped_non_1v1 = 0
    duplicates = []
    for team in teams:
        members = team.get("teamMembers", [])
        if len(members) != 1:
            skipped_non_1v1 += 1  # this project analyzes 1v1 only
            continue
        m = members[0]
        player_key = f"{m['region']}:{m['realm']}:{m['id']}"
        # Each player has one ladder entry per race they play. Missing race -> 'unknown'.
        race = m.get("favoriteRace") or "unknown"

        # Insert the player if new; otherwise refresh their latest name/clan/race.
        conn.execute(
            """
            INSERT INTO players (player_key, region_id, realm, profile_id, display_name, clan_tag)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_key) DO UPDATE SET
                display_name = excluded.display_name,
                clan_tag = COALESCE(excluded.clan_tag, players.clan_tag)
            """,
            (player_key, m["region"], m["realm"], str(m["id"]),
             m.get("displayName"), m.get("clanTag")),
        )

        result = conn.execute(
            """
            INSERT OR IGNORE INTO ladder_entries
                (snapshot_id, player_key, race, mmr, points, wins, losses, previous_rank, join_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (snapshot_id, player_key, race, team.get("mmr"), team.get("points"), team.get("wins"),
             team.get("losses"), team.get("previousRank"), team.get("joinTimestamp")),
        )
        if result.rowcount == 1:
            loaded += 1
        else:
            # Same player AND same race listed twice in one pull: keep the first, report the rest.
            duplicates.append(f"{player_key} ({m.get('displayName')}, mmr={team.get('mmr')})")

    note = ""
    if skipped_non_1v1:
        note += f", {skipped_non_1v1} non-1v1 teams skipped"
    if duplicates:
        note += f", {len(duplicates)} duplicate entries ignored (first 3: {'; '.join(duplicates[:3])})"
    return f"loaded {loaded} rows from {path.name}{note}"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    files = sorted(RAW_DIR.glob("*.json"))
    if not files:
        print(f"No JSON files found in {RAW_DIR}. Run src/fetch_grandmaster.py first.")
        return

    for path in files:
        print(load_file(conn, path))
    conn.commit()

    print("\nRow counts now in the database:")
    for table in ("players", "snapshots", "ladder_entries"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count}")
    conn.close()
    print(f"\nDatabase saved at: {DB_PATH}")


if __name__ == "__main__":
    main()
