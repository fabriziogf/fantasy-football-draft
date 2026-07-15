"""Draft state: the ordered list of picks, snake-draft math, and persistence.

Picks are recorded in draft order (every team's pick, FR-11). Because the draft
is a snake, the overall pick numbers that belong to *my* slot are fully
determined by the league shape, so "my roster" is derived, not entered.

State persists to ``processed/draft_state.json`` after every mutation so a crash
or refresh mid-draft can recover (NFR-4).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict

from .. import config

_STATE_PATH = config.PROCESSED_DIR / "draft_state.json"


def snake_pick_order(num_teams: int, rounds: int) -> list[int]:
    """Team slot (1-indexed) on the clock for each overall pick, in order."""
    order: list[int] = []
    for r in range(rounds):
        slots = range(1, num_teams + 1)
        order.extend(slots if r % 2 == 0 else reversed(slots))
    return order


@dataclass
class DraftState:
    my_slot: int
    num_teams: int = config.NUM_TEAMS
    rounds: int = field(default_factory=lambda: sum(config.STARTERS.values()) + config.BENCH_SLOTS)
    # Player keys in draft order (index 0 == overall pick #1).
    picked: list[str] = field(default_factory=list)

    # --- snake geometry ---------------------------------------------------
    @property
    def pick_order(self) -> list[int]:
        return snake_pick_order(self.num_teams, self.rounds)

    @property
    def my_pick_overalls(self) -> list[int]:
        """1-indexed overall pick numbers that belong to my slot."""
        return [i + 1 for i, slot in enumerate(self.pick_order) if slot == self.my_slot]

    @property
    def picks_made(self) -> int:
        return len(self.picked)

    @property
    def current_overall(self) -> int:
        """1-indexed pick about to be made."""
        return self.picks_made + 1

    @property
    def on_the_clock(self) -> int:
        """Team slot currently on the clock (0 if draft complete)."""
        order = self.pick_order
        idx = self.picks_made
        return order[idx] if idx < len(order) else 0

    @property
    def is_my_pick(self) -> bool:
        return self.on_the_clock == self.my_slot

    def my_next_overall(self) -> int | None:
        """Overall number of my next pick at or after the current pick."""
        return next((p for p in self.my_pick_overalls if p >= self.current_overall), None)

    def my_following_overall(self) -> int | None:
        """Overall number of my pick *after* the current one (for VONA horizon)."""
        return next((p for p in self.my_pick_overalls if p > self.current_overall), None)

    @property
    def my_picked_keys(self) -> list[str]:
        mine = set(self.my_pick_overalls)
        return [key for i, key in enumerate(self.picked) if (i + 1) in mine]

    @property
    def rounds_left(self) -> int:
        return len(self.my_pick_overalls) - len(self.my_picked_keys)

    # --- mutations --------------------------------------------------------
    def pick(self, key: str) -> None:
        if key in self.picked:
            raise ValueError(f"{key!r} already drafted")
        self.picked.append(key)

    def undo(self) -> str | None:
        return self.picked.pop() if self.picked else None

    # --- persistence ------------------------------------------------------
    def save(self) -> None:
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        _STATE_PATH.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "DraftState | None":
        if not _STATE_PATH.exists():
            return None
        data = json.loads(_STATE_PATH.read_text())
        return cls(**data)

    @classmethod
    def clear(cls) -> None:
        _STATE_PATH.unlink(missing_ok=True)
