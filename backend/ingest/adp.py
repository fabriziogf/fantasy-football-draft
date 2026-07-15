"""Ingest Average Draft Position (ADP) from Fantasy Football Calculator.

FFC exposes a free, public JSON endpoint parameterized by scoring format, team
count, and year. We use it as *market ordering* to place players our historical
model can't project (rookies, K, DST) and to drive draft-time VONA later.

Normalization to nflverse conventions happens here so the rest of the app sees a
single vocabulary:
  - positions: PK -> K, DEF -> DST
  - teams:     LAR -> LA (only divergence in the 2026 set)
  - names:     a stripped/lowercased key for joining to projections
"""
from __future__ import annotations

import json
import re
import urllib.request

import pandas as pd

from .. import config

FFC_URL = (
    "https://fantasyfootballcalculator.com/api/v1/adp/"
    "{scoring}?teams={teams}&year={year}"
)
# FFC 403s the default urllib UA; present a browser-like one.
_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

POSITION_MAP = {"PK": "K", "DEF": "DST"}
TEAM_MAP = {"LAR": "LA"}

_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}

# Explicit nickname fixes where FFC and nflverse disagree on a veteran's first
# name. Keyed by the *normalized* FFC name -> normalized nflverse name. Kept
# curated (not fuzzy) so we never accidentally collapse two distinct players
# (e.g. a rookie who merely shares a last name). Extend as new mismatches surface.
NAME_ALIASES = {
    "kenny gainwell": "kenneth gainwell",
}


def normalize_name(name: str) -> str:
    """Lowercased, punctuation-stripped, suffix-free key for joining names.

    'Amon-Ra St. Brown' -> 'amonra st brown'; 'Michael Pittman Jr.' -> 'michael pittman'.
    Applies NAME_ALIASES so known nickname mismatches join correctly.
    """
    if not isinstance(name, str):
        return ""
    s = name.lower().replace(".", "").replace("'", "").replace("-", "")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    tokens = [t for t in s.split() if t and t not in _SUFFIXES]
    key = " ".join(tokens)
    return NAME_ALIASES.get(key, key)


def load_adp(scoring: str = "ppr", teams: int | None = None, year: int | None = None,
             use_cache: bool = True) -> pd.DataFrame:
    """Return a normalized ADP frame, cached to data/raw/adp_<...>.parquet.

    Columns: player_id_ffc, name, name_key, position, team, adp, adp_stdev,
             adp_high, adp_low, times_drafted, bye
    """
    teams = teams or config.NUM_TEAMS
    year = year or config.DRAFT_SEASON
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = config.RAW_DIR / f"adp_{scoring}_{teams}_{year}.parquet"

    if use_cache and cache.exists():
        return pd.read_parquet(cache)

    url = FFC_URL.format(scoring=scoring, teams=teams, year=year)
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req) as resp:
        payload = json.load(resp)
    if payload.get("status") != "Success":
        raise RuntimeError(f"FFC ADP fetch failed: {payload.get('errors', payload)}")

    rows = []
    for p in payload["players"]:
        pos = POSITION_MAP.get(p["position"], p["position"])
        team = TEAM_MAP.get(p["team"], p["team"])
        rows.append(
            {
                "player_id_ffc": p.get("player_id"),
                "name": p.get("name"),
                "name_key": normalize_name(p.get("name", "")),
                "position": pos,
                "team": team,
                "adp": p.get("adp"),
                "adp_stdev": p.get("stdev"),
                "adp_high": p.get("high"),
                "adp_low": p.get("low"),
                "times_drafted": p.get("times_drafted"),
                "bye": p.get("bye"),
            }
        )
    df = pd.DataFrame(rows).sort_values("adp").reset_index(drop=True)
    df.to_parquet(cache, index=False)
    return df
