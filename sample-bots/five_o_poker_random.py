"""Uniform-random bot for Five-O Poker (Five-O)."""

from __future__ import annotations

import random

from vibewarz import FiveOPokerBot, FiveOPokerPlaceAction, FiveOPokerState


class FiveOPokerRandomBot(FiveOPokerBot):
    display_name = "FiveOPokerRandomBot"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def act(self, state: FiveOPokerState):
        legal = self.legal_actions(state)
        if not legal:
            return FiveOPokerPlaceAction(column=0)  # shouldn't be reached
        return self._rng.choice(legal)
