"""FastAPI app: draft board, live draft state, and recommendations.

Run (from repo root):
    backend/.venv/bin/uvicorn backend.api.app:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .. import config
from .data import load_board
from .draft_state import DraftState
from .recommender import recommend
from .schemas import PickRequest, SetupRequest, StateResponse

# In-memory draft state, restored from disk on startup (NFR-4).
_state: DraftState | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _state
    load_board()
    _state = DraftState.load()
    yield


app = FastAPI(title="Fantasy Football Draft Assistant", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev tool
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_state() -> DraftState:
    if _state is None:
        raise HTTPException(status_code=409, detail="Draft not set up. POST /setup first.")
    return _state


def _clean(records) -> list[dict]:
    """JSON-safe records (NaN -> None)."""
    df = pd.DataFrame(records)
    return df.replace({np.nan: None}).to_dict("records") if not df.empty else []


def _player_rows(keys: list[str]) -> list[dict]:
    board = load_board()
    cols = ["key", "name", "position", "team", "bye", "tier", "pos_rank",
            "proj_points", "vor", "adp"]
    idx = {k: i for i, k in enumerate(keys)}
    sub = board[board["key"].isin(keys)]
    sub = sub.assign(_o=sub["key"].map(idx)).sort_values("_o")
    return _clean(sub[cols].to_dict("records"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "board_players": len(load_board())}


@app.get("/config")
def get_config() -> dict:
    return {
        "num_teams": config.NUM_TEAMS,
        "starters": config.STARTERS,
        "bench": config.BENCH_SLOTS,
        "draft_season": config.DRAFT_SEASON,
    }


@app.get("/board")
def get_board(
    available_only: bool = False,
    position: str | None = None,
    limit: int = Query(300, ge=1, le=1000),
) -> list[dict]:
    board = load_board()
    if available_only and _state is not None:
        board = board[~board["key"].isin(set(_state.picked))]
    if position:
        board = board[board["position"] == position.upper()]
    return _clean(board.head(limit).to_dict("records"))


@app.post("/setup", response_model=StateResponse)
def setup(req: SetupRequest) -> StateResponse:
    global _state
    kwargs = {"my_slot": req.my_slot}
    if req.num_teams is not None:
        kwargs["num_teams"] = req.num_teams
    if req.rounds is not None:
        kwargs["rounds"] = req.rounds
    _state = DraftState(**kwargs)
    _state.save()
    return _state_response()


@app.get("/state", response_model=StateResponse)
def get_state() -> StateResponse:
    _require_state()
    return _state_response()


@app.post("/pick", response_model=StateResponse)
def make_pick(req: PickRequest) -> StateResponse:
    state = _require_state()
    board = load_board()
    if req.key not in set(board["key"]):
        raise HTTPException(status_code=404, detail=f"Unknown player key: {req.key}")
    try:
        state.pick(req.key)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    state.save()
    return _state_response()


@app.post("/undo", response_model=StateResponse)
def undo() -> StateResponse:
    state = _require_state()
    removed = state.undo()
    if removed is None:
        raise HTTPException(status_code=409, detail="No picks to undo.")
    state.save()
    return _state_response()


@app.get("/recommend")
def get_recommendations(limit: int = Query(10, ge=1, le=50)) -> dict:
    state = _require_state()
    board = load_board()
    recs = recommend(board, state, limit=limit)
    return {
        "on_the_clock": state.on_the_clock,
        "is_my_pick": state.is_my_pick,
        "my_next_overall": state.my_next_overall(),
        "recommendations": recs,
    }


def _state_response() -> StateResponse:
    state = _require_state()
    recent = list(reversed(state.picked[-10:]))
    return StateResponse(
        my_slot=state.my_slot,
        num_teams=state.num_teams,
        rounds=state.rounds,
        picks_made=state.picks_made,
        current_overall=state.current_overall,
        on_the_clock=state.on_the_clock,
        is_my_pick=state.is_my_pick,
        my_next_overall=state.my_next_overall(),
        rounds_left=state.rounds_left,
        my_roster=_player_rows(state.my_picked_keys),
        recent_picks=_player_rows(recent),
    )
