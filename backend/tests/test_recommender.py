"""Recommender tests on a synthetic board so behavior is deterministic."""
import pandas as pd
import pytest

from backend.api.draft_state import DraftState
from backend.api.recommender import recommend


def _player(key, name, pos, rank, points, vor, adp, repl, tier=1):
    return {
        "key": key, "name": name, "position": pos, "pos_rank": rank,
        "proj_points": points, "vor": vor, "adp": adp,
        "replacement_points": repl, "tier": tier, "team": "XXX", "bye": 7,
    }


@pytest.fixture
def board():
    rows = [
        _player("wr1|WR", "WR One", "WR", 1, 280, 100, 3, 180),
        _player("wr2|WR", "WR Two", "WR", 2, 270, 90, 8, 180),
        _player("wr3|WR", "WR Three", "WR", 3, 260, 80, 15, 180),
        _player("wr4|WR", "WR Four", "WR", 4, 250, 70, 40, 180),
        _player("rb1|RB", "RB One", "RB", 1, 260, 95, 5, 165),
        _player("rb2|RB", "RB Two", "RB", 2, 250, 85, 12, 165),
        _player("rb3|RB", "RB Three", "RB", 3, 240, 75, 30, 165),
        _player("qb1|QB", "QB One", "QB", 1, 330, 96, 35, 233),
        _player("te1|TE", "TE One", "TE", 1, 195, 45, 45, 150),
        _player("k1|K", "K One", "K", 1, 150, 5, 130, 128),
        _player("dst1|DST", "DST One", "DST", 1, 130, 5, 95, 108),
    ]
    return pd.DataFrame(rows)


def _state_with_roster(board, positions, my_slot=1, num_teams=12):
    """Build a state whose derived roster has the given positions."""
    st = DraftState(my_slot=my_slot, num_teams=num_teams, rounds=15)
    picks = st.my_pick_overalls
    picked = ["filler|XX"] * (max(picks[: len(positions)]))
    key_by_pos = {}
    for _, r in board.iterrows():
        key_by_pos.setdefault(r["position"], []).append(r["key"])
    for i, pos in enumerate(positions):
        picked[picks[i] - 1] = key_by_pos[pos].pop(0)
    st.picked = picked
    return st


def test_phase_a_prioritizes_rb_wr_over_kdst(board):
    st = DraftState(my_slot=1, num_teams=12, rounds=15)  # empty roster
    recs = recommend(board, st, limit=11)
    top3 = {r["position"] for r in recs[:3]}
    assert top3 <= {"RB", "WR"}
    # K/DST are pushed to the very bottom.
    positions = [r["position"] for r in recs]
    assert positions.index("K") >= len(positions) - 2
    assert positions.index("DST") >= len(positions) - 2


def test_carveout_allows_elite_qb(board):
    # Empty roster: elite QB (VOR 96) beats best available RB/WR VOR (100? no -> 96<100)
    # so with default it should NOT outrank the top WR, but should still appear
    # above K/DST via the carve-out multiplier.
    st = DraftState(my_slot=1, num_teams=12, rounds=15)
    recs = recommend(board, st, limit=11)
    qb_idx = [r["position"] for r in recs].index("QB")
    k_idx = [r["position"] for r in recs].index("K")
    assert qb_idx < k_idx


def test_phase_b_shifts_to_need(board):
    # Roster already has 3 WR + 2 RB -> phase B; QB/TE (unfilled) should beat more WR.
    st = _state_with_roster(board, ["WR", "WR", "WR", "RB", "RB"])
    recs = recommend(board, st, limit=10)
    positions = [r["position"] for r in recs]
    assert "QB" in positions and "TE" in positions
    # A needed QB/TE ranks above leftover WR depth.
    first_need = min(positions.index("QB"), positions.index("TE"))
    if "WR" in positions:
        assert first_need < positions.index("WR")


def test_vona_flags_scarcity(board):
    st = DraftState(my_slot=1, num_teams=12, rounds=15)
    recs = {r["key"]: r for r in recommend(board, st, limit=11)}
    # WR1 (adp 3) is gone before my next pick -> positive VONA cliff.
    assert recs["wr1|WR"]["vona"] > 0
