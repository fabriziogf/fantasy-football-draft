"""Pydantic request/response models for the draft API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SetupRequest(BaseModel):
    my_slot: int = Field(..., ge=1, description="My draft slot (1-indexed).")
    num_teams: int | None = Field(None, ge=2)
    rounds: int | None = Field(None, ge=1)


class PickRequest(BaseModel):
    key: str = Field(..., description="Board player key to mark drafted.")


class StateResponse(BaseModel):
    my_slot: int
    num_teams: int
    rounds: int
    picks_made: int
    current_overall: int
    on_the_clock: int
    is_my_pick: bool
    my_next_overall: int | None
    rounds_left: int
    my_roster: list[dict]
    recent_picks: list[dict]
