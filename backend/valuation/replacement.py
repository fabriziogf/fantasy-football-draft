"""Replacement level and Value Over Replacement (VOR).

Replacement level for a position is the projected points of the *last starter*
the league will roster at that position — i.e. the best player you could get
"for free" because someone at that position is always available. A player's value
is how far above that baseline they project.

Starter demand per position = teams * starters, plus a share of the league's FLEX
spots (config.FLEX_ALLOCATION) added to RB/WR/TE.
"""
from __future__ import annotations

import pandas as pd

from .. import config


def replacement_ranks() -> dict[str, int]:
    """1-indexed rank of the replacement-level player at each draft position."""
    teams = config.NUM_TEAMS
    flex_total = teams * config.STARTERS.get("FLEX", 0)
    ranks: dict[str, int] = {}
    for pos in config.DRAFT_POSITIONS:
        base = teams * config.STARTERS.get(pos, 0)
        flex = flex_total * config.FLEX_ALLOCATION.get(pos, 0.0)
        ranks[pos] = max(1, round(base + flex))
    return ranks


def add_vor(board: pd.DataFrame) -> pd.DataFrame:
    """Add ``pos_rank``, ``replacement_points``, and ``vor`` columns."""
    board = board.copy()
    ranks = replacement_ranks()

    board["pos_rank"] = (
        board.groupby("position")["proj_points"]
        .rank(ascending=False, method="first")
        .astype(int)
    )

    repl_points: dict[str, float] = {}
    for pos, grp in board.groupby("position"):
        ordered = grp.sort_values("proj_points", ascending=False)["proj_points"].to_numpy()
        idx = min(ranks.get(pos, len(ordered)), len(ordered)) - 1
        repl_points[pos] = float(ordered[idx])

    board["replacement_points"] = board["position"].map(repl_points)
    board["vor"] = (board["proj_points"] - board["replacement_points"]).round(1)
    return board
