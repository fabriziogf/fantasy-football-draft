"""Draft-time recommendations: blend value (VOR) and scarcity (VONA), then apply
the FR-10 roster strategy, and explain each pick.

VONA (value over next available) is the marginal reason to draft a player *now*
rather than wait: their projected points minus the best player at that position
likely to survive to your next pick (estimated from ADP). A big VONA means a
cliff is coming; a small VONA means you can wait.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config
from .draft_state import DraftState

_BASE_STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DST": 1}
_FLEX_ELIGIBLE = set(config.FLEX_POSITIONS)


def _survivor_baseline(avail: pd.DataFrame, horizon: int | None) -> dict[str, float]:
    """Best projected points per position likely to survive to my next pick.

    A player survives if their ADP is at/after the horizon (or they have no ADP,
    meaning the market isn't drafting them). With no horizon (draft nearly over)
    or no survivors, fall back to the position's replacement level.
    """
    baseline: dict[str, float] = {}
    for pos, grp in avail.groupby("position"):
        repl = float(grp["replacement_points"].iloc[0])
        if horizon is None:
            baseline[pos] = repl
            continue
        survivors = grp[grp["adp"].isna() | (grp["adp"] >= horizon)]
        baseline[pos] = float(survivors["proj_points"].max()) if not survivors.empty else repl
    return baseline


def _roster_counts(board: pd.DataFrame, my_keys: list[str]) -> dict[str, int]:
    mine = board[board["key"].isin(my_keys)]
    return mine["position"].value_counts().to_dict()


def _unmet_need(pos: str, counts: dict[str, int]) -> bool:
    """Does this position still have an unfilled starter slot (incl. FLEX)?"""
    if counts.get(pos, 0) < _BASE_STARTERS.get(pos, 0):
        return True
    if pos in _FLEX_ELIGIBLE:
        flex_used = sum(max(0, counts.get(p, 0) - _BASE_STARTERS[p]) for p in _FLEX_ELIGIBLE)
        if flex_used < config.STARTERS.get("FLEX", 0):
            return True
    return False


def _multiplier(row, phase_a, counts, best_skill_metric, rounds_left) -> float:
    pos = row["position"]
    if phase_a:
        if pos in ("RB", "WR"):
            return config.NEED_MULT_PHASE_A[pos]
        if pos in ("QB", "TE"):
            carve = (
                row["pos_rank"] <= config.STRATEGY_CARVEOUT_RANK
                and row[config.STRATEGY_CARVEOUT_METRIC] > best_skill_metric
            )
            return 1.0 if carve else config.NEED_MULT_PHASE_A[pos]
        return config.NEED_MULT_PHASE_A[pos]  # K/DST

    # phase B: roster-need filling
    if pos in ("K", "DST"):
        if _unmet_need(pos, counts) and rounds_left <= config.KDST_LAST_ROUNDS:
            return config.NEED_MULT_PHASE_B_NEEDED
        return config.NEED_MULT_KDST_EARLY
    return config.NEED_MULT_PHASE_B_NEEDED if _unmet_need(pos, counts) else config.NEED_MULT_PHASE_B_DEPTH


def _reason(row, vona, phase_a, needed, horizon, carve) -> str:
    bits = [f"{row['position']}{int(row['pos_rank'])}", f"Tier {int(row['tier'])}",
            f"VOR {row['vor']:.0f}"]
    if vona >= 8 and horizon is not None:
        bits.append(f"cliff: next comparable at pick {horizon} is ~{vona:.0f} pts worse")
    elif horizon is not None and vona <= 2:
        bits.append("similar value should survive to your next pick")
    if carve:
        bits.append("elite value beats the board despite position")
    elif phase_a and row["position"] in ("RB", "WR"):
        bits.append("builds RB/WR core")
    elif needed:
        bits.append("fills a starting need")
    return " · ".join(bits)


def recommend(board: pd.DataFrame, state: DraftState, limit: int = 10) -> list[dict]:
    drafted = set(state.picked)
    avail = board[~board["key"].isin(drafted)].copy()
    if avail.empty:
        return []

    horizon = state.my_following_overall()  # who's gone before I pick again
    baseline = _survivor_baseline(avail, horizon)
    counts = _roster_counts(board, state.my_picked_keys)

    n_rb, n_wr = counts.get("RB", 0), counts.get("WR", 0)
    phase_a = n_rb < config.STRATEGY_TARGET_RB or n_wr < config.STRATEGY_TARGET_WR

    skill = avail[avail["position"].isin(("RB", "WR"))]
    best_skill_metric = float(skill[config.STRATEGY_CARVEOUT_METRIC].max()) if not skill.empty else 0.0

    rows = []
    for _, row in avail.iterrows():
        pos = row["position"]
        vona = round(float(row["proj_points"]) - baseline.get(pos, row["replacement_points"]), 1)
        core = config.REC_VOR_WEIGHT * row["vor"] + config.REC_VONA_WEIGHT * vona
        mult = _multiplier(row, phase_a, counts, best_skill_metric, state.rounds_left)
        score = round(core * mult, 2)

        carve = (
            phase_a and pos in ("QB", "TE")
            and row["pos_rank"] <= config.STRATEGY_CARVEOUT_RANK
            and row[config.STRATEGY_CARVEOUT_METRIC] > best_skill_metric
        )
        needed = _unmet_need(pos, counts)
        rows.append(
            {
                "key": row["key"],
                "name": row["name"],
                "position": pos,
                "team": row.get("team"),
                "bye": None if pd.isna(row.get("bye")) else int(row["bye"]),
                "tier": int(row["tier"]),
                "pos_rank": int(row["pos_rank"]),
                "proj_points": round(float(row["proj_points"]), 1),
                "vor": round(float(row["vor"]), 1),
                "vona": vona,
                "adp": None if pd.isna(row.get("adp")) else float(row["adp"]),
                "score": score,
                "reason": _reason(row, vona, phase_a, needed, horizon, carve),
            }
        )

    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows[:limit]
