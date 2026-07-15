"""Transparent risk and bye-week flags for a candidate pick (FR-15).

Everything here is rule-based and explainable — no black-box risk score. Each
flag is a ``{code, label}`` the UI can show, plus an overall ``risk`` level
derived from how many fired. Bye-week conflicts are reported separately because
they depend on your current roster, not the player alone.
"""
from __future__ import annotations

import math

from .. import config


def _num(v):
    """Return a float or None (treats NaN/None uniformly)."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def risk_flags(row: dict) -> list[dict]:
    """Player-intrinsic risk flags (independent of roster)."""
    flags: list[dict] = []
    pos = row.get("position")

    if row.get("proj_source") == "adp_imputed":
        flags.append({"code": "rookie", "label": "Rookie — value from market ADP, no NFL history"})

    # Durability: low games-per-season over the history window.
    games = _num(row.get("total_games"))
    seasons = _num(row.get("seasons_played"))
    if games is not None and seasons and seasons >= 2:
        avg = games / seasons
        if avg < config.RISK_DURABILITY_AVG_GAMES:
            flags.append(
                {"code": "durability", "label": f"Missed time — ~{avg:.0f} games/yr recently"}
            )

    # Age-cliff risk by position.
    age = _num(row.get("age"))
    threshold = config.RISK_AGE.get(pos)
    if age is not None and threshold is not None and age >= threshold:
        flags.append({"code": "age", "label": f"{pos} age {age:.0f} — age-cliff risk"})

    # Market volatility: wide ADP spread.
    stdev = _num(row.get("adp_stdev"))
    adp = _num(row.get("adp"))
    if stdev is not None and adp:
        if stdev >= config.RISK_ADP_STDEV_MIN and stdev >= config.RISK_ADP_STDEV_RATIO * adp:
            flags.append({"code": "volatile", "label": "Volatile ADP — market disagrees on value"})

    return flags


def bye_conflict(row: dict, roster: list[dict]) -> dict | None:
    """Flag if this player shares a bye with a rostered player at the same position."""
    bye = _num(row.get("bye"))
    if bye is None:
        return None
    clashes = [
        p["name"]
        for p in roster
        if p.get("position") == row.get("position") and _num(p.get("bye")) == bye
    ]
    if not clashes:
        return None
    return {"bye": int(bye), "with": clashes,
            "label": f"Bye {int(bye)} clashes with {', '.join(clashes)}"}


def assess(row: dict, roster: list[dict]) -> dict:
    """Full assessment: risk level + flags + optional bye conflict."""
    flags = risk_flags(row)
    level = "high" if len(flags) >= 2 else "medium" if flags else "low"
    conflict = bye_conflict(row, roster)
    return {"risk": level, "flags": flags, "bye_conflict": conflict}
