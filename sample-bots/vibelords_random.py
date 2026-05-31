"""Uniform-random over legal actions — Vibelords leaderboard floor."""

from __future__ import annotations

import random

from vibewarz import Bot
from vibewarz_games.vibelords.game import Vibelords


class VibelordsRandomBot(Bot):
    game = "vibelords"
    display_name = "VibelordsRandomBot"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._engine = Vibelords()

    def act(self, state):
        legal = self._engine.legal_actions(state, self.seat)
        return self._rng.choice(legal) if legal else {"type": "noop"}
