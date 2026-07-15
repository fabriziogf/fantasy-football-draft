"""Fill projected points for players our stat model can't score.

Two gaps to fill on the merged board:

  * **Rookies** (skill positions with an ADP but no NFL history) — imputed from a
    monotonic, per-position ADP -> points curve fit on players who have *both* a
    model projection and an ADP. This market-anchors rookies onto the same points
    scale as our projections, at their own position.
  * **K / DST** — no model data exists at all, so they use the documented per-rank
    baseline in ``config.KDST_BASELINE``.

Every filled value is tagged in a ``proj_source`` column for transparency:
``model`` | ``adp_imputed`` | ``baseline_kdst``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config


def _isotonic_decreasing(y: np.ndarray) -> np.ndarray:
    """Pool-adjacent-violators fit of a non-increasing sequence (unit weights)."""
    y = y.astype(float).copy()
    n = len(y)
    # Work on the negated series as a non-decreasing isotonic fit.
    vals = -y
    level_val = list(vals)
    level_wt = [1.0] * n
    i = 0
    # Standard PAV over a stack of pooled blocks.
    blocks: list[list[float]] = []  # each: [value, weight, count]
    for v in vals:
        blocks.append([v, 1.0, 1])
        while len(blocks) > 1 and blocks[-2][0] >= blocks[-1][0]:
            v2, w2, c2 = blocks.pop()
            v1, w1, c1 = blocks.pop()
            merged_val = (v1 * w1 + v2 * w2) / (w1 + w2)
            blocks.append([merged_val, w1 + w2, c1 + c2])
    out = []
    for val, _w, cnt in blocks:
        out.extend([val] * cnt)
    return -np.array(out)


def _position_curve(matched: pd.DataFrame):
    """Return a callable adp -> points for one position, or None if too sparse."""
    m = matched.dropna(subset=["adp", "proj_points"]).sort_values("adp")
    if len(m) < 3:
        return None
    xs = m["adp"].to_numpy(dtype=float)
    ys = _isotonic_decreasing(m["proj_points"].to_numpy(dtype=float))
    # np.interp clamps to endpoint values outside [xs.min, xs.max], which is the
    # behavior we want for very early/late ADPs.
    return lambda a: float(np.interp(a, xs, ys))


def impute_points(board: pd.DataFrame) -> pd.DataFrame:
    """Add ``proj_points`` (filled) and ``proj_source`` to the merged board."""
    board = board.copy()
    board["proj_source"] = np.where(board["proj_points"].notna(), "model", None)

    # --- Skill-position rookies: per-position ADP curve --------------------
    for pos in config.PROJECTED_POSITIONS:
        pos_mask = board["position"] == pos
        matched = board[pos_mask & board["proj_points"].notna()]
        curve = _position_curve(matched)
        need = pos_mask & board["proj_points"].isna() & board["adp"].notna()
        if curve is None or not need.any():
            continue
        board.loc[need, "proj_points"] = board.loc[need, "adp"].map(curve)
        board.loc[need, "proj_source"] = "adp_imputed"

    # --- K / DST: per-rank baseline ---------------------------------------
    for pos, params in config.KDST_BASELINE.items():
        pos_mask = board["position"] == pos
        if not pos_mask.any():
            continue
        # Rank by ADP (best ADP = rank 1); fall back to arbitrary order if no ADP.
        ranked = board.loc[pos_mask].sort_values("adp", na_position="last")
        ranks = np.arange(len(ranked))
        pts = params["top"] - params["decay"] * ranks
        board.loc[ranked.index, "proj_points"] = pts
        board.loc[ranked.index, "proj_source"] = "baseline_kdst"

    return board
