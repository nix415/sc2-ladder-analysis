# StarCraft II Grandmaster Ladder Analysis

An end-to-end data project: pull ranked ladder data from a live API, store and clean it in SQL, and present the findings in an interactive dashboard.

**Live dashboard:** [View on Tableau Public](https://public.tableau.com/views/Book1_17954684206350/StarCraftIIGrandmasterLadderRaceandRatingPatterns)

**Tools:** Python (requests, pandas), SQL (SQLite: joins, CTEs, window functions), Tableau Public

> Not affiliated with or endorsed by Blizzard Entertainment. Data comes from Blizzard's public Battle.net API.

---

## The question in plain language

In a competitive game where players choose between several playable "races," do the choices players make and the results they get differ by region and by race? This project looks at three things for the top tier of players:

1. Which races are most common in each region?
2. Do win rates differ by race?
3. How are skill ratings (MMR) distributed in each region?

## Data

- **Source:** Blizzard Battle.net API, Grandmaster ladder (the top tier of ranked 1v1 play) for the US, EU, and Korea.
- **Snapshot:** pulled once on 2026-11-20.
- **Size:** 587 ladder entries from 573 unique players. After removing entries with fewer than 20 games, 552 entries remain.
- **What one row means:** one player on one race. The ladder tracks rating and wins/losses separately for each race a player uses, so a player who plays two races appears twice.

## Method

1. **Collect:** Python script authenticates with OAuth and pulls the Grandmaster ladder for each region, saving the raw JSON (`src/get_token.py`, `src/fetch_grandmaster.py`).
2. **Store:** A loader builds a normalized SQLite database with three tables: `players`, `snapshots`, `ladder_entries` (`sql/01_schema.sql`, `src/load_to_db.py`).
3. **Clean and validate:**
   - The loader flagged 14 apparently duplicate rows. Inspecting them (`src/inspect_duplicates.py`) showed they were not errors: they were the same player on different races. I changed the table design so one row is one player per race, which recovered all 14 rows.
   - Entries with fewer than 20 games were excluded from the analysis because ratings and win rates based on so few games are unreliable.
   - Entries with a missing race value were labeled "unknown" and excluded from the charts (3 entries).
4. **Analyze:** Exploratory queries using joins, aggregation, and window functions (`sql/02_explore.sql`).
5. **Visualize:** An anonymized CSV (player names and clan tags removed, players replaced by hashed IDs) feeds the Tableau dashboard (`src/export_for_tableau.py`).

## Findings

*Based on the 2026-11-20 snapshot, entries with 20+ games.*

- **Protoss is the most common race in all three regions**: about 43% of entries in EU, 37% in KR, and 39% in the US.
- **Win rates are close across races**: roughly 53.7% (random) to 55.4% (zerg). Every race is above 50% because these are top-ranked players, so this does not show that any race is stronger. I have not tested whether the small gaps are statistically meaningful.
- **Rating distributions are bottom-heavy**: in all three regions most entries sit just above the tier's cutoff rating, with a long thin tail toward the highest ratings. The cutoff differs by region (roughly 4,500 in EU, 4,300 in the US, and 3,800 in KR), so average ratings should not be compared across regions as a measure of strength.

## Limitations

- **One snapshot, one tier.** This is a single pull of only the top tier, so it cannot show trends over time or compare skill levels.
- **Small sample.** About 550 entries is too few for strong statistical conclusions, and the "random" race has far fewer entries than the others.
- **Entries, not games.** The API gives per-player season totals, not individual matches, so matchup-level questions (for example, one race against another) cannot be answered with this data.
- **Observational data.** Nothing here shows why patterns occur.

## Next steps

- Pull the ladder on a schedule to build history and study change over time.
- Add lower leagues to compare skill tiers.
- Test whether the win-rate differences are statistically significant, accounting for the fact that games from the same player are not independent.

## Reproduce it

1. Create a Blizzard developer client at the [Battle.net developer portal](https://community.developer.battle.net/access/clients) to get a Client ID and Secret.
2. Set up the project:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your Client ID and Secret. Never commit this file.
4. Run the pipeline from the project folder:
   ```
   python src/fetch_grandmaster.py
   python src/load_to_db.py
   python src/run_sql.py sql/02_explore.sql
   python src/export_for_tableau.py
   ```

## Repository layout

```
sc2-ladder-analysis/
├── README.md
├── requirements.txt
├── .env.example           # template for credentials (the real .env is not committed)
├── src/                   # Python: API access, loading, exports
├── sql/                   # schema and analysis queries
└── data/processed/        # anonymized CSV used by the dashboard
```
