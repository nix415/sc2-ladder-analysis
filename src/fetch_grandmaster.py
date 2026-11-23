"""Pull the Grandmaster ladder for each region and save the raw JSON.

Run from the project root:
    python src/fetch_grandmaster.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from get_token import get_token

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Blizzard region IDs: 1 = US, 2 = EU, 3 = KR
REGIONS = {"us": 1, "eu": 2, "kr": 3}


def fetch_grandmaster(region_name: str, region_id: int, token: str) -> dict:
    url = f"https://{region_name}.api.blizzard.com/sc2/ladder/grandmaster/{region_id}"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    token = get_token()
    pulled_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for region_name, region_id in REGIONS.items():
        print(f"Fetching Grandmaster ladder for {region_name.upper()}...")
        data = fetch_grandmaster(region_name, region_id, token)

        out_path = RAW_DIR / f"grandmaster_{region_name}_{pulled_at}.json"
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"  Saved to {out_path}")

        # Quick look at the structure so you can see the real field names.
        print(f"  Top-level keys: {list(data.keys())}")
        teams = data.get("ladderTeams", [])
        print(f"  Number of teams returned: {len(teams)}")
        if teams:
            print("  First record:")
            print(json.dumps(teams[0], indent=4))

        time.sleep(1)  # be polite to the API


if __name__ == "__main__":
    main()
