"""Ingest historical player data from nflverse (via nfl_data_py).

Pulls seasonal offensive stats and roster metadata (name/position/team/age),
joins them, caches the raw pull to parquet, and returns a tidy frame keyed by
(player_id, season).
"""
from __future__ import annotations

import warnings

import pandas as pd

from .. import config

warnings.filterwarnings("ignore")  # nfl_data_py is chatty about dtypes


def _import():
    # Imported lazily so the rest of the app doesn't require the dependency.
    import nfl_data_py as nfl

    return nfl


def load_seasonal_stats(seasons: list[int] | None = None, use_cache: bool = True) -> pd.DataFrame:
    """Return per-(player, season) offensive stats joined with name/position.

    Caches the raw joined pull to ``data/raw/seasonal_<seasons>.parquet``.
    """
    seasons = seasons or config.HISTORY_SEASONS
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = config.RAW_DIR / f"seasonal_{min(seasons)}_{max(seasons)}.parquet"

    if use_cache and cache.exists():
        return pd.read_parquet(cache)

    nfl = _import()

    # Fetch season by season so a single unavailable year (e.g. one the mirror
    # hasn't published yet) doesn't sink the whole pull.
    available = []
    frames = []
    for yr in seasons:
        try:
            frames.append(nfl.import_seasonal_data([yr]))
            available.append(yr)
        except Exception as exc:  # noqa: BLE001 - want to skip and continue
            print(f"[ingest] season {yr} unavailable, skipping ({exc})")
    if not frames:
        raise RuntimeError(f"No seasonal data available for {seasons}")
    stats = pd.concat(frames, ignore_index=True)

    # Roster metadata for name/position/team/age, one row per player-season.
    rosters = nfl.import_seasonal_rosters(available)
    meta_cols = ["player_id", "season", "player_name", "position", "team", "age"]
    meta_cols = [c for c in meta_cols if c in rosters.columns]
    meta = rosters[meta_cols].drop_duplicates(subset=["player_id", "season"])

    df = stats.merge(meta, on=["player_id", "season"], how="left")
    df.to_parquet(cache, index=False)
    return df
