"""Assign draft tiers within each position.

Tiers capture "cliffs" — groups of comparable players separated by a meaningful
drop in projected points. Walking each position from the top, a new tier starts
when the gap to the previous player exceeds a percentile of that position's own
inter-player gaps, so the threshold adapts to each position's scale.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config


def add_tiers(board: pd.DataFrame) -> pd.DataFrame:
    """Add a 1-indexed ``tier`` column (per position)."""
    board = board.copy()
    board["tier"] = 1

    for pos, grp in board.groupby("position"):
        ordered = grp.sort_values("proj_points", ascending=False)
        pts = ordered["proj_points"].to_numpy(dtype=float)
        if len(pts) < 2:
            continue
        gaps = -np.diff(pts)  # positive drops between consecutive players
        threshold = np.percentile(gaps, config.TIER_GAP_PERCENTILE)
        # Guard degenerate case where most gaps are zero.
        threshold = max(threshold, 1e-9)

        tier = 1
        tiers = [1]
        for g in gaps:
            if g > threshold:
                tier += 1
            tiers.append(tier)
        board.loc[ordered.index, "tier"] = tiers

    return board
