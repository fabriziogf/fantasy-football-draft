"""Run the full pipeline: ingest -> projections -> valuation board.

Writes ``processed/projections.csv`` and ``processed/board.csv``.

Usage (from repo root):
    backend/.venv/bin/python -m backend.run_pipeline [--no-cache]
"""
from __future__ import annotations

import argparse

from . import config
from .projections.baseline import build_projections
from .valuation.board import build_board


def main() -> None:
    parser = argparse.ArgumentParser(description="Build projections + draft board.")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Re-fetch raw data (stats + ADP) instead of using cached files.",
    )
    args = parser.parse_args()
    use_cache = not args.no_cache

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    proj = build_projections(use_cache=use_cache)
    proj_out = config.PROCESSED_DIR / "projections.csv"
    proj.to_csv(proj_out, index=False)
    print(f"Wrote {len(proj)} player projections -> {proj_out}")

    board = build_board(use_cache=use_cache)
    board_out = config.PROCESSED_DIR / "board.csv"
    board.to_csv(board_out, index=False)
    print(f"Wrote {len(board)} draftable players -> {board_out}")

    print("\nTop 25 by VOR:")
    cols = ["overall_rank", "name", "position", "team", "proj_points",
            "proj_source", "vor", "pos_rank", "tier", "adp"]
    print(board[cols].head(25).to_string(index=False))


if __name__ == "__main__":
    main()
