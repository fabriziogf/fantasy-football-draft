import numpy as np
import pandas as pd
import pytest

from backend import config
from backend.ingest.adp import normalize_name
from backend.valuation.imputation import _isotonic_decreasing
from backend.valuation.replacement import add_vor, replacement_ranks
from backend.valuation.tiers import add_tiers


def test_normalize_name_and_aliases():
    assert normalize_name("Amon-Ra St. Brown") == "amonra st brown"
    assert normalize_name("Michael Pittman Jr.") == "michael pittman"
    # Curated nickname alias resolves to the nflverse spelling.
    assert normalize_name("Kenny Gainwell") == "kenneth gainwell"


def test_replacement_ranks_include_flex():
    r = replacement_ranks()
    # 12 teams: RB/WR = 2 starters*12 + half of 12 flex = 24 + 6 = 30.
    assert r["RB"] == 30
    assert r["WR"] == 30
    assert r["QB"] == 12
    assert r["TE"] == 12
    assert r["K"] == 12
    assert r["DST"] == 12


def test_isotonic_decreasing_is_monotonic():
    y = np.array([10.0, 12.0, 8.0, 9.0, 5.0, 6.0, 1.0])
    fit = _isotonic_decreasing(y)
    assert np.all(np.diff(fit) <= 1e-9)
    # Fit preserves the total (pooling conserves mean).
    assert fit.sum() == pytest.approx(y.sum())


def test_add_vor_uses_replacement_point():
    # 31 RBs with descending points; replacement rank for RB is 30.
    pts = list(np.linspace(300, 100, 31))
    df = pd.DataFrame({"position": ["RB"] * 31, "proj_points": pts})
    out = add_vor(df)
    repl = sorted(pts, reverse=True)[29]  # 30th best
    assert out["replacement_points"].iloc[0] == pytest.approx(repl)
    top = out.sort_values("proj_points", ascending=False).iloc[0]
    assert top["vor"] == pytest.approx(round(300 - repl, 1))


def test_tiers_start_at_one_and_increase_downward():
    # Distinct gaps so the top cliff clearly exceeds the 75th-percentile gap.
    df = pd.DataFrame(
        {"position": ["WR"] * 5, "proj_points": [200.0, 197.0, 150.0, 148.0, 100.0]}
    )
    out = add_tiers(df).sort_values("proj_points", ascending=False)
    tiers = out["tier"].tolist()
    assert tiers[0] == 1
    assert tiers == sorted(tiers)  # non-decreasing as points fall
    assert out["tier"].max() > 1   # a real cliff created a new tier
