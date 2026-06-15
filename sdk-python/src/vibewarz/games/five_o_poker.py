"""Typed SDK models for Five-O Poker bots."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from ..bot import ActionResult, Bot
from .base import ActionModel, StateModel

FiveOPokerPhase = Literal["placing", "done"]


class FiveOPokerPlaceAction(ActionModel):
    type: Literal["place"] = "place"
    column: int


# Placement is the only action in this one-and-done game.
FiveOPokerAction = FiveOPokerPlaceAction


class FiveOPokerPlayer(StateModel):
    seat: int
    columns: list[list[str]] = Field(default_factory=list)
    last_action: FiveOPokerAction | dict[str, object] | None = None


class FiveOPokerHistoryEntry(StateModel):
    seat: int
    action: FiveOPokerAction | dict[str, object]


class FiveOPokerState(StateModel):
    tick: int
    phase: FiveOPokerPhase
    deck: list[str] = Field(default_factory=list)
    action_on: int | None
    players: list[FiveOPokerPlayer]
    history: list[FiveOPokerHistoryEntry] = Field(default_factory=list)
    history_delta: list[FiveOPokerHistoryEntry] = Field(default_factory=list)
    placement: list[int] = Field(default_factory=list)
    winner: int | None = None
    showdown_hands: dict[str, list[str]] | None = None
    winning_columns: dict[str, list[int]] | None = None
    current_drawn_card: str | None = None

    def player(self, seat: int) -> FiveOPokerPlayer:
        for player in self.players:
            if player.seat == seat:
                return player
        raise KeyError(f"seat {seat} not found")


class FiveOPokerBot(Bot):
    """Base class for typed Five-O Poker bots."""

    game = "five_o_poker"
    state_model: ClassVar[type[FiveOPokerState]] = FiveOPokerState

    def on_start(self, initial_state: FiveOPokerState) -> None:
        """Called once at game_start."""

    def act(self, state: FiveOPokerState) -> ActionResult:
        raise NotImplementedError


__all__ = [
    "FiveOPokerAction",
    "FiveOPokerPlaceAction",
    "FiveOPokerPlayer",
    "FiveOPokerHistoryEntry",
    "FiveOPokerPhase",
    "FiveOPokerState",
    "FiveOPokerBot",
]
