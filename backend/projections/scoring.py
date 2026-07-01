"""Convert raw stat lines into fantasy points under the league's scoring rules."""
from __future__ import annotations

import pandas as pd

from .. import config


def fantasy_points(df: pd.DataFrame) -> pd.Series:
    """Compute PPR fantasy points for each row of a seasonal-stats frame.

    Missing stat columns are treated as zero so the function is robust to the
    exact column set nflverse returns.
    """
    pts = pd.Series(0.0, index=df.index)

    for col, weight in config.SCORING.items():
        if col == "fumbles_lost":
            continue
        if col in df.columns:
            pts = pts + df[col].fillna(0) * weight

    # Fumbles lost are spread across several stat-group columns; sum them.
    fumbles = pd.Series(0.0, index=df.index)
    for col in config.FUMBLE_LOST_COLUMNS:
        if col in df.columns:
            fumbles = fumbles + df[col].fillna(0)
    pts = pts + fumbles * config.SCORING["fumbles_lost"]

    return pts
