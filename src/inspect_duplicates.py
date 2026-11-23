"""Show players who appear more than once in the same ladder file, side by side.

Run from the project root:
    python src/inspect_duplicates.py
"""

import json
from collections import defaultdict
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main() -> None:
    files = sorted(RAW_DIR.glob("*.json"))
    if not files:
        print(f"No JSON files in {RAW_DIR}. Run src/fetch_grandmaster.py first.")
        return

    total_dupes = 0
    for path in files:
        teams = json.loads(path.read_text(encoding="utf-8")).get("ladderTeams", [])

        # Group every entry in this file by player key.
        by_player = defaultdict(list)
        for position, team in enumerate(teams, start=1):
            for m in team.get("teamMembers", []):
                key = f"{m['region']}:{m['realm']}:{m['id']}"
                by_player[key].append((position, m, team))

        dupes = {k: v for k, v in by_player.items() if len(v) > 1}
        total_dupes += len(dupes)
        print(f"\n=== {path.name}: {len(dupes)} players listed more than once ===")

        for key, entries in dupes.items():
            print(f"\nPlayer {key}")
            for position, m, team in entries:
                print(
                    f"  list position {position:>3} | name={m.get('displayName')} | race={m.get('favoriteRace')} "
                    f"| mmr={team.get('mmr')} | points={team.get('points')} "
                    f"| W-L={team.get('wins')}-{team.get('losses')} "
                    f"| team size={len(team.get('teamMembers', []))} | joined={team.get('joinTimestamp')}"
                )

    print(f"\nTotal players with duplicate entries across all files: {total_dupes}")


if __name__ == "__main__":
    main()
