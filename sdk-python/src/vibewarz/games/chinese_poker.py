"""Typed SDK models for Chinese Poker (Five-O) bots."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from ..bot import ActionResult, Bot
from .base import ActionModel, StateModel

ChinesePokerPhase = Literal["placing", "done"]


class ChinesePokerPlaceAction(ActionModel):
    type: Literal["place"] = "place"
    column: int


# Placement is the only action in this one-and-done game.
ChinesePokerAction = ChinesePokerPlaceAction


class ChinesePokerPlayer(StateModel):
    seat: int
    columns: list[list[str]] = Field(default_factory=list)
    last_action: ChinesePokerAction | dict[str, object] | None = None


class ChinesePokerHistoryEntry(StateModel):
    seat: int
    action: ChinesePokerAction | dict[str, object]


class ChinesePokerState(StateModel):
    tick: int
    phase: ChinesePokerPhase
    deck: list[str] = Field(default_factory=list)
    action_on: int | None
    players: list[ChinesePokerPlayer]
    history: list[ChinesePokerHistoryEntry] = Field(default_factory=list)
    history_delta: list[ChinesePokerHistoryEntry] = Field(default_factory=list)
    placement: list[int] = Field(default_factory=list)
    winner: int | None = None
    showdown_hands: dict[str, list[str]] | None = None
    winning_columns: dict[str, list[int]] | None = None
    current_drawn_card: str | None = None

    def player(self, seat: int) -> ChinesePokerPlayer:
        for player in self.players:
            if player.seat == seat:
                return player
        raise KeyError(f"seat {seat} not found")


class ChinesePokerBot(Bot):
    """Base class for typed Chinese Poker bots."""

    game = "chinese_poker"
    state_model: ClassVar[type[ChinesePokerState]] = ChinesePokerState

    def on_start(self, initial_state: ChinesePokerState) -> None:
        """Called once at game_start."""

    def act(self, state: ChinesePokerState) -> ActionResult:
        raise NotImplementedError


__all__ = [
    "ChinesePokerAction",
    "ChinesePokerPlaceAction",
    "ChinesePokerPlayer",
    "ChinesePokerHistoryEntry",
    "ChinesePokerPhase",
    "ChinesePokerState",
    "ChinesePokerBot",
]
