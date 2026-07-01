"""Projection tests. Uses the cached raw pull if present; skips otherwise so
the suite stays runnable offline / in CI without network access."""
import pandas as pd
import pytest

from backend import config
from backend.projections.baseline import build_projections

_CACHE = config.RAW_DIR / (
    f"seasonal_{min(config.HISTORY_SEASONS)}_{max(config.HISTORY_SEASONS)}.parquet"
)

pytestmark = pytest.mark.skipif(
    not _CACHE.exists(), reason="no cached raw data; run the pipeline first"
)


@pytest.fixture(scope="module")
def proj() -> pd.DataFrame:
    return build_projections(use_cache=True)


def test_expected_columns(proj):
    expected = {
        "player_id", "player_name", "position", "team", "age",
        "proj_points", "proj_ppg", "total_games", "seasons_played",
    }
    assert expected.issubset(proj.columns)


def test_only_projected_positions(proj):
    assert set(proj["position"].unique()).issubset(set(config.PROJECTED_POSITIONS))


def test_no_missing_projections(proj):
    assert proj["proj_points"].notna().all()
    assert (proj["proj_points"] >= 0).all()


def test_sorted_descending(proj):
    assert proj["proj_points"].is_monotonic_decreasing


def test_shrinkage_controls_small_samples(proj):
    # No one with a tiny sample should out-project the very top of the board.
    tiny = proj[proj["total_games"] <= 3]
    if not tiny.empty:
        assert tiny["proj_points"].max() < proj["proj_points"].max()
