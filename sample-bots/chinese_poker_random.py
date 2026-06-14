"""Uniform-random bot for Chinese Poker (Five-O)."""

from __future__ import annotations

import random

from vibewarz import ChinesePokerBot, ChinesePokerCheckAction, ChinesePokerState


class ChinesePokerRandomBot(ChinesePokerBot):
    display_name = "ChinesePokerRandomBot"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def act(self, state: ChinesePokerState):
        legal = self.legal_actions(state)
        if not legal:
            return ChinesePokerCheckAction()  # safety fallback
        return self._rng.choice(legal)
