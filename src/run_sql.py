"""Run the queries in a .sql file against the project database and print the results.

Run from the project root:
    python src/run_sql.py sql/02_explore.sql
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "sc2.db"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python src/run_sql.py sql/02_explore.sql")
        return
    sql_path = Path(sys.argv[1])
    if not DB_PATH.exists():
        print("No database found. Run: python src/load_to_db.py")
        return

    conn = sqlite3.connect(DB_PATH)
    pd.set_option("display.width", 200)

    buffer = ""
    title = ""
    for line in sql_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- Q"):
            title = line[3:].strip()
        if line.strip().startswith("--") and not buffer:
            continue
        buffer += line + "\n"
        if sqlite3.complete_statement(buffer):
            print(f"\n=== {title} ===")
            print(pd.read_sql_query(buffer, conn).to_string(index=False))
            buffer = ""
    conn.close()


if __name__ == "__main__":
    main()
