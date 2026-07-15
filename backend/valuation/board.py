"""Build the unified draft board: projections + ADP -> VOR, tiers, ranks.

Pipeline:
  1. Load model projections and FFC ADP.
  2. Outer-merge on (normalized name, position) so we keep both matched veterans
     and ADP-only rookies / K / DST.
  3. Impute points for players the model can't score (rookies via ADP curve,
     K/DST via baseline).
  4. Compute replacement level and VOR; assign tiers.
  5. Keep the draftable universe (anyone with an ADP, or any model player at or
     above replacement) and rank overall by VOR.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config
from ..ingest.adp import load_adp, normalize_name
from ..projections.baseline import build_projections
from .imputation import impute_points, _isotonic_decreasing
from .replacement import add_vor
from .tiers import add_tiers


def _merge_sources(proj: pd.DataFrame, adp: pd.DataFrame) -> pd.DataFrame:
    proj = proj.copy()
    proj["name_key"] = proj["player_name"].map(normalize_name)

    merged = proj.merge(
        adp, on=["name_key", "position"], how="outer", suffixes=("_proj", "_adp")
    )

    # Reconcile display fields, preferring model metadata then ADP metadata.
    merged["name"] = merged["player_name"].fillna(merged["name"])
    merged["team"] = merged["team_proj"].fillna(merged["team_adp"])
    merged = merged.drop(columns=["player_name", "team_proj", "team_adp"], errors="ignore")
    return merged


def _anchor_kdst_to_market(board: pd.DataFrame) -> pd.DataFrame:
    """Re-express K/DST value via the market instead of their invented points.

    We have no real projection for K or DST, so their raw VOR (derived from a
    coarse baseline) can't be compared across positions — left alone it drafts
    them far too early. Instead we map each K/DST's ADP through the skill-position
    ADP -> VOR curve, so a defense/kicker is worth what the market pays for a
    skill player drafted at the same slot. This lands them in their true draft
    range. Their ``proj_points``/``tier`` (from the baseline) remain for display
    and intra-position ordering only.
    """
    board = board.copy()
    skill = board[
        board["position"].isin(config.PROJECTED_POSITIONS)
        & board["adp"].notna()
        & board["vor"].notna()
    ].sort_values("adp")
    if len(skill) < 3:
        return board
    xs = skill["adp"].to_numpy(dtype=float)
    ys = _isotonic_decreasing(skill["vor"].to_numpy(dtype=float))

    mask = board["position"].isin(("K", "DST")) & board["adp"].notna()
    board.loc[mask, "vor"] = (
        board.loc[mask, "adp"].map(lambda a: float(np.interp(a, xs, ys))).round(1)
    )
    return board


def build_board(use_cache: bool = True) -> pd.DataFrame:
    proj = build_projections(use_cache=use_cache)
    adp = load_adp(use_cache=use_cache)

    board = _merge_sources(proj, adp)
    board = board[board["position"].isin(config.DRAFT_POSITIONS)].copy()

    board = impute_points(board)
    board = add_vor(board)
    board = _anchor_kdst_to_market(board)
    board = add_tiers(board)

    # Draftable universe: everyone with a market ADP, plus model players who
    # project at or above replacement (sleepers the market may be missing).
    draftable = board["adp"].notna() | (board["vor"] >= 0)
    board = board[draftable].copy()

    # Overall ordering by value; ADP as a tiebreaker/reference.
    board["overall_rank"] = (
        board["vor"].rank(ascending=False, method="first").astype(int)
    )
    board = board.sort_values("overall_rank").reset_index(drop=True)

    cols = [
        "overall_rank", "name", "position", "team", "bye", "age",
        "proj_points", "proj_source", "vor", "pos_rank", "tier",
        "adp", "adp_stdev", "replacement_points", "player_id",
    ]
    cols = [c for c in cols if c in board.columns]
    return board[cols]


if __name__ == "__main__":
    b = build_board()
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = config.PROCESSED_DIR / "board.csv"
    b.to_csv(out, index=False)
    print(f"Wrote {len(b)} players -> {out}\n")
    show = ["overall_rank", "name", "position", "team", "proj_points",
            "proj_source", "vor", "pos_rank", "tier", "adp"]
    print(b[show].head(30).to_string(index=False))
