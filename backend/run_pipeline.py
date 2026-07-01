"""Run the Phase 1 pipeline: ingest -> projections -> processed/projections.csv.

Usage (from repo root):
    backend/.venv/bin/python -m backend.run_pipeline [--no-cache]
"""
from __future__ import annotations

import argparse

from . import config
from .projections.baseline import build_projections


def main() -> None:
    parser = argparse.ArgumentParser(description="Build draft-season projections.")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Re-fetch raw data instead of using the cached parquet.",
    )
    args = parser.parse_args()

    proj = build_projections(use_cache=not args.no_cache)

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = config.PROCESSED_DIR / "projections.csv"
    proj.to_csv(out, index=False)

    print(f"Wrote {len(proj)} player projections -> {out}")
    print("\nTop 20 (PPR):")
    cols = ["player_name", "position", "team", "proj_points", "proj_ppg"]
    print(proj[cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
