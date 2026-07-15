"""Load the draft board for the API, building it on demand if missing."""
from __future__ import annotations

import pandas as pd

from .. import config

_BOARD_PATH = config.PROCESSED_DIR / "board.csv"
_board: pd.DataFrame | None = None


def load_board(refresh: bool = False) -> pd.DataFrame:
    """Return the board DataFrame (cached in-process).

    Reads ``processed/board.csv`` if present, otherwise builds it. Pass
    ``refresh=True`` to rebuild from source data.
    """
    global _board
    if _board is not None and not refresh:
        return _board

    if refresh or not _BOARD_PATH.exists():
        from ..valuation.board import build_board

        _board = build_board(use_cache=not refresh)
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        _board.to_csv(_BOARD_PATH, index=False)
    else:
        _board = pd.read_csv(_BOARD_PATH)
    return _board
