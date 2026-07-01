"""Baseline season projections for the draft season.

Transparent, explainable starting point:

  1. Compute PPR fantasy points for each player-season.
  2. Convert to points-per-game (PPG) to neutralize injury-shortened seasons.
  3. Take a recency-weighted average of PPG across the history window,
     renormalizing weights over the seasons each player actually played.
  4. Shrink that PPG toward a low position prior by sample size, so players with
     only a game or two of hot rate stats don't get extrapolated to a full season.
  5. Project season points = shrunk PPG * EXPECTED_GAMES.

This is deliberately simple and tunable. A richer model (or externally imported
projections) can be dropped in behind the same output contract:

    columns -> [player_id, player_name, position, team, age,
                proj_points, proj_ppg, seasons_played]
"""
from __future__ import annotations

import pandas as pd

from .. import config
from ..ingest.nflverse import load_seasonal_stats
from .scoring import fantasy_points


def _weighted_ppg(group: pd.DataFrame) -> pd.Series:
    """Recency-weighted PPG for one player across their available seasons."""
    weights = group["season"].map(config.SEASON_WEIGHTS).fillna(0.0)
    total_w = weights.sum()
    if total_w <= 0:
        # No configured weight (shouldn't happen) -> simple mean.
        ppg = group["ppg"].mean()
    else:
        ppg = float((group["ppg"] * weights).sum() / total_w)

    # Metadata comes from the most recent season the player appears in.
    latest = group.sort_values("season").iloc[-1]
    return pd.Series(
        {
            "player_name": latest.get("player_name"),
            "position": latest.get("position"),
            "team": latest.get("team"),
            "age": latest.get("age"),
            "raw_ppg": ppg,
            "total_games": float(group["games"].sum()),
            "seasons_played": int(group["season"].nunique()),
        }
    )


def _apply_shrinkage(proj: pd.DataFrame) -> pd.DataFrame:
    """Regress each player's raw PPG toward a low, position-specific prior.

    The prior is a fraction of the median PPG among established players at that
    position (those with at least SHRINKAGE_GAMES total games). Players with few
    games are pulled hard toward the prior; established players barely move.
    """
    established = proj[proj["total_games"] >= config.SHRINKAGE_GAMES]
    pos_median = established.groupby("position")["raw_ppg"].median()
    # Fallback to the overall median for any position with no established pool.
    overall_prior = proj["raw_ppg"].median() * config.PRIOR_FRACTION

    prior = proj["position"].map(pos_median).fillna(proj["raw_ppg"].median())
    prior = prior * config.PRIOR_FRACTION
    prior = prior.fillna(overall_prior)

    k = config.SHRINKAGE_GAMES
    g = proj["total_games"]
    proj["proj_ppg"] = (g * proj["raw_ppg"] + k * prior) / (g + k)
    return proj


def build_projections(use_cache: bool = True) -> pd.DataFrame:
    """Return draft-season projections for offensive skill players."""
    df = load_seasonal_stats(config.HISTORY_SEASONS, use_cache=use_cache)

    df = df.copy()
    df["fantasy_points"] = fantasy_points(df)

    games = df["games"].fillna(0) if "games" in df.columns else pd.Series(0, index=df.index)
    # Guard against divide-by-zero; drop zero-game rows (no signal).
    df = df[games > 0].copy()
    df["ppg"] = df["fantasy_points"] / df["games"]

    # Keep only fantasy-relevant offensive positions.
    df = df[df["position"].isin(config.PROJECTED_POSITIONS)]

    proj = (
        df.groupby("player_id", group_keys=True)
        .apply(_weighted_ppg, include_groups=False)
        .reset_index()
    )
    proj = _apply_shrinkage(proj)
    proj["proj_points"] = (proj["proj_ppg"] * config.EXPECTED_GAMES).round(1)
    proj["proj_ppg"] = proj["proj_ppg"].round(2)

    proj = proj[
        [
            "player_id",
            "player_name",
            "position",
            "team",
            "age",
            "proj_points",
            "proj_ppg",
            "total_games",
            "seasons_played",
        ]
    ]
    return proj.sort_values("proj_points", ascending=False).reset_index(drop=True)
