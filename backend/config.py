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

# All positions that appear on the draft board.
DRAFT_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DST")

# How the league's FLEX starters are expected to be spent across positions, used
# when computing replacement level (a flex spot deepens RB/WR starter demand).
FLEX_ALLOCATION = {"RB": 0.5, "WR": 0.5, "TE": 0.0}

# ---------------------------------------------------------------------------
# K / DST baseline projections
# ---------------------------------------------------------------------------
# nflverse offensive data has no K or DST scoring, so these two positions can't
# come from our stat model. Their fantasy-point spread is small and well-known,
# so we place them on a simple, documented per-rank baseline: the rank-r player
# scores ``top - decay * (r - 1)`` points. This is a coarse domain-knowledge
# anchor (not an imported projection set); a data-driven K/DST model built from
# play-by-play is a future improvement. Values only need to be roughly right
# because K/DST are drafted late and have shallow tiers.
KDST_BASELINE = {
    "K": {"top": 150.0, "decay": 2.0},
    "DST": {"top": 130.0, "decay": 2.0},
}

# ---------------------------------------------------------------------------
# Tiers
# ---------------------------------------------------------------------------
# A new tier starts when the projected-points gap to the previous player at that
# position exceeds this percentile of the position's inter-player gaps. Higher =
# fewer, coarser tiers.
TIER_GAP_PERCENTILE = 75

# ---------------------------------------------------------------------------
# Recommender (Phase 3)
# ---------------------------------------------------------------------------
# A pick's core score blends static value (VOR) with scarcity (VONA: value over
# the best player at the position likely to survive to your next pick).
REC_VOR_WEIGHT = 0.5
REC_VONA_WEIGHT = 0.5

# FR-10 strategy: accumulate this many RB/WR before shifting to roster-need
# filling. Until then, RB/WR are prioritized and QB/TE/K/DST are damped.
STRATEGY_TARGET_RB = 2
STRATEGY_TARGET_WR = 3

# Positional multipliers applied to the core score.
#   phase A = still accumulating the RB/WR core (FR-10).
#   phase B = roster-need filling.
NEED_MULT_PHASE_A = {
    "RB": 1.0, "WR": 1.0,   # the core we're building
    "QB": 0.5, "TE": 0.5,   # allowed only via the top-3 value carve-out below
    "K": 0.1, "DST": 0.1,   # essentially off the board early
}
# Phase B multipliers by whether the position still has an unfilled starter slot.
NEED_MULT_PHASE_B_NEEDED = 1.0
NEED_MULT_PHASE_B_DEPTH = 0.4
# K/DST stay suppressed until the final rounds even when a slot is open.
NEED_MULT_KDST_EARLY = 0.2
KDST_LAST_ROUNDS = 3  # boost K/DST to full only within this many rounds of the end

# Carve-out (FR-10): in phase A, a top-N QB/TE earns full priority only if it
# beats the best available RB/WR on this metric. "vor" reads the requirement's
# "outscore" as value-over-replacement (raw points always favor QBs), so the
# carve-out fires on genuine value, not position. Set to "proj_points" for a
# literal points comparison.
STRATEGY_CARVEOUT_RANK = 3
STRATEGY_CARVEOUT_METRIC = "vor"


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
