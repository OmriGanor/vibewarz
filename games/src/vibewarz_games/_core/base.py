"""Game ABC, GameMeta, StepResult.

Every game in vibewarz subclasses `Game` and provides a pure `step` function
mapping (state, actions) -> StepResult. The server engine wraps these and
drives the match loop.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GameMeta:
    id: str
    display_name: str
    min_players: int
    max_players: int
    # Max time the engine waits per tick for an action to arrive before
    # substituting `default_action`. Per-seat timeout, not a wall-clock floor.
    tick_deadline_ms: int = 50
    # Target wall-clock tick cadence when a match runs in realtime mode (i.e.
    # any seat is interactive). In fast mode this is ignored; ticks race at
    # action-arrival speed. Typically equal to tick_deadline_ms.
    tick_interval_ms: int = 50
    max_ticks: int = 1500
    description: str = ""
    # Aggregation window for variable-sized tables. When a queue first
    # reaches `min_players`, the matchmaker waits up to this long for
    # more players to arrive before popping (capping at `max_players`).
    # Pops fire early if `max_players` is reached. Set to 0 for fixed-
    # size games (e.g. Curve) where min == max — they pop immediately.
    match_wait_ms: int = 0


@dataclass(frozen=True)
class StepResult:
    state: dict
    done: bool = False
    placement: list[int] | None = None
    reason: str | None = None
    eliminated_this_tick: tuple[int, ...] = ()


class Game(ABC):
    """Authoritative game interface.

    Implementations MUST be pure (no mutation of inputs, no I/O, no globals).
    Randomness comes only from the `seed` argument to `initial_state`.
    """

    meta: GameMeta

    @abstractmethod
    def initial_state(self, seed: int, num_players: int) -> dict:
        ...

    @abstractmethod
    def alive_seats(self, state: dict) -> list[int]:
        ...

    @abstractmethod
    def legal_actions(self, state: dict, seat: int) -> list[dict]:
        ...

    @abstractmethod
    def is_legal(self, state: dict, seat: int, action: dict) -> bool:
        ...

    @abstractmethod
    def default_action(self, state: dict, seat: int) -> dict:
        ...

    @abstractmethod
    def step(self, state: dict, actions: dict[int, dict]) -> StepResult:
        ...

    def acting_seats(self, state: dict) -> list[int]:
        """Seats whose action the engine should solicit this step.

        Default: every alive seat — the simultaneous-move semantics Curve
        uses. Turn-based games (e.g. poker) override this to return only the
        seat(s) on the clock, so non-acting players observe `tick_result`
        broadcasts without receiving a `tick_request` they can't answer.
        """
        return self.alive_seats(state)

    def view_for(self, state: dict, seat: int) -> dict:
        """Per-seat view of state. Default: a shallow copy with `seed` removed
        — appropriate for public-information games where the only secret is
        the RNG seed itself.

        Hidden-information games (poker hole cards, fog of war, etc.) override
        this to strip additional fields owned by other seats; overrides MUST
        also omit `seed`. The unredacted state is retained for replay
        journaling and the next engine step; the redacted view is the only
        thing that travels over the wire to that seat.

        Why `seed` is server-only: the RNG is deterministic, so any client
        that learns the seed can locally reproduce the engine and predict
        future events (e.g. opponents' hole cards in poker).
        """
        return {k: v for k, v in state.items() if k != "seed"}

    def render_ascii(self, state: dict) -> str:
        return ""
