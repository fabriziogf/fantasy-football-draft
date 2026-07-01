"""Central configuration: league settings, scoring, and paths.

Everything tunable about the league lives here so model code never hard-codes
rules. Change these values to re-target a different league.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# ---------------------------------------------------------------------------
# Season / draft target
# ---------------------------------------------------------------------------
DRAFT_SEASON = 2026
# Seasons of history used to build projections, most-recent last.
# NOTE: the nflverse mirror currently publishes through 2024; seasons that are
# unavailable are skipped gracefully during ingest.
HISTORY_SEASONS = [2022, 2023, 2024]
# Weight applied to each history season. Recent seasons count more. Weights are
# renormalized over whichever seasons a player actually has data for.
SEASON_WEIGHTS = {2022: 0.2, 2023: 0.3, 2024: 0.5}
# Games assumed in the projected season. Slightly below the 17-game max to
# price in typical availability/injury attrition.
EXPECTED_GAMES = 16

# Sample-size shrinkage. A player's weighted PPG is regressed toward a low
# position prior; the fewer games they've actually played, the harder the pull.
#   shrunk = (total_games * ppg + SHRINKAGE_GAMES * prior) / (total_games + SHRINKAGE_GAMES)
# SHRINKAGE_GAMES acts as a pseudo-count (roughly "how many games of prior").
SHRINKAGE_GAMES = 10
# Prior PPG per position = this fraction of the position's median PPG among
# established players (those with >= SHRINKAGE_GAMES total games in the window).
PRIOR_FRACTION = 0.5

# ---------------------------------------------------------------------------
# League structure
# ---------------------------------------------------------------------------
NUM_TEAMS = 12
# Starting lineup slots. FLEX draws from RB/WR/TE.
STARTERS = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLEX": 1,
    "K": 1,
    "DST": 1,
}
FLEX_POSITIONS = ("RB", "WR", "TE")
BENCH_SLOTS = 6

# Positions the projection model currently covers (offensive skill players).
# K and DST are streamed/late and handled separately in a later phase.
PROJECTED_POSITIONS = ("QB", "RB", "WR", "TE")

# ---------------------------------------------------------------------------
# Scoring (PPR)
# ---------------------------------------------------------------------------
SCORING = {
    # Passing
    "passing_yards": 0.04,        # 1 pt / 25 yds
    "passing_tds": 4.0,
    "interceptions": -2.0,
    "passing_2pt_conversions": 2.0,
    # Rushing
    "rushing_yards": 0.1,         # 1 pt / 10 yds
    "rushing_tds": 6.0,
    "rushing_2pt_conversions": 2.0,
    # Receiving (PPR)
    "receptions": 1.0,
    "receiving_yards": 0.1,
    "receiving_tds": 6.0,
    "receiving_2pt_conversions": 2.0,
    # Turnovers (fumbles lost, summed across stat groups)
    "fumbles_lost": -2.0,
}

# Stat columns that make up "fumbles_lost" in the nflverse seasonal data.
FUMBLE_LOST_COLUMNS = (
    "sack_fumbles_lost",
    "rushing_fumbles_lost",
    "receiving_fumbles_lost",
)
