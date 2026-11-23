"""Request an OAuth access token from Battle.net using the client credentials flow."""

import os

import requests
from dotenv import load_dotenv

TOKEN_URL = "https://oauth.battle.net/token"


def get_token() -> str:
    """Return a fresh access token (valid ~24 hours)."""
    load_dotenv()
    client_id = os.getenv("BLIZZARD_CLIENT_ID")
    client_secret = os.getenv("BLIZZARD_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing credentials. Copy .env.example to .env and fill in "
            "BLIZZARD_CLIENT_ID and BLIZZARD_CLIENT_SECRET."
        )

    response = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


if __name__ == "__main__":
    token = get_token()
    # Print only a short prefix so the full token never lands in your terminal history.
    print(f"Success! Got a token starting with: {token[:6]}...")
