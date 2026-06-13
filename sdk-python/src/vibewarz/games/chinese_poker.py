"""Typed SDK models for Chinese Poker (Five-O) bots."""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ..bot import ActionResult, Bot
from .base import ActionModel, StateModel

ChinesePokerPhase = Literal[
    "placing",
    "betting",
    "showdown",
    "hand_complete",
    "done",
]


class ChinesePokerPlaceAction(ActionModel):
    type: Literal["place"] = "place"
    column: int


class ChinesePokerFoldAction(ActionModel):
    type: Literal["fold"] = "fold"


class ChinesePokerCheckAction(ActionModel):
    type: Literal["check"] = "check"


class ChinesePokerCallAction(ActionModel):
    type: Literal["call"] = "call"


class ChinesePokerRaiseAction(ActionModel):
    type: Literal["raise"] = "raise"
    to: int


ChinesePokerAction = Annotated[
    ChinesePokerPlaceAction
    | ChinesePokerFoldAction
    | ChinesePokerCheckAction
    | ChinesePokerCallAction
    | ChinesePokerRaiseAction,
    Field(discriminator="type"),
]


class ChinesePokerPlayer(StateModel):
    seat: int
    stack: int
    in_tournament: bool
    in_hand: bool
    columns: list[list[str]] = Field(default_factory=list)
    folded: bool
    all_in: bool
    committed_round: int
    committed_hand: int
    last_action: ChinesePokerAction | dict[str, object] | None = None


class ChinesePokerPotDistribution(StateModel):
    seat: int
    amount: int


class ChinesePokerHistoryEntry(StateModel):
    hand: int
    phase: str
    seat: int
    action: ChinesePokerAction | dict[str, object]


class ChinesePokerState(StateModel):
    tick: int
    hand_number: int
    phase: ChinesePokerPhase
    button: int
    deck: list[str] = Field(default_factory=list)
    pot: int
    current_bet: int
    min_raise: int
    action_on: int | None
    acted_this_round: list[int] = Field(default_factory=list)
    players: list[ChinesePokerPlayer]
    history: list[ChinesePokerHistoryEntry] = Field(default_factory=list)
    history_delta: list[ChinesePokerHistoryEntry] = Field(default_factory=list)
    placement: list[int] = Field(default_factory=list)
    pot_distribution: list[ChinesePokerPotDistribution] | None = None
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
    "ChinesePokerFoldAction",
    "ChinesePokerCheckAction",
    "ChinesePokerCallAction",
    "ChinesePokerRaiseAction",
    "ChinesePokerPlayer",
    "ChinesePokerPotDistribution",
    "ChinesePokerHistoryEntry",
    "ChinesePokerPhase",
    "ChinesePokerState",
    "ChinesePokerBot",
]
