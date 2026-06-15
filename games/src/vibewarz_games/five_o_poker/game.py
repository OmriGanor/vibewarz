"""Five-O Poker game implementation.

A single-deal, 2-player game where players build five 5-card hands (columns).
It is "one and done" — there is no betting and no chips; one full board is
built and a single showdown decides the winner.

1. Deal: 5 cards dealt face-up (1 per column) to each player.
2. Pacing: players alternate, drawing 1 card at a time and placing it in any
   column. A card may only go in one of the currently-shortest columns, so
   the columns are filled level-by-level and stay within one card of each
   other.
3. Visibility: the 4th card of each column (index ``HIDDEN_CARD_INDEX``) is
   dealt face-down — redacted from the opponent's view until showdown. The
   5th card is face-up.
4. Showdown: once both boards are full (25 cards each) the five columns are
   compared head-to-head. Winning the most columns takes the game; winning
   all five is a "Five-O" scoop. Equal columns won is a draw.
"""

from __future__ import annotations

from typing import Final

from .._core.base import Game, GameMeta, StepResult
from .._core.registry import register
from ..poker.betting import new_shuffled_deck
from ..poker.hand_eval import rank

NUM_COLUMNS: Final = 5
CARDS_PER_COLUMN: Final = 5
TOTAL_CARDS: Final = NUM_COLUMNS * CARDS_PER_COLUMN * 2  # both boards full
HIDDEN_CARD_INDEX: Final = 3  # 4th card per column is dealt face-down


@register
class FiveOPoker(Game):
    meta = GameMeta(
        id="five_o_poker",
        display_name="Five-O Poker",
        min_players=2,
        max_players=2,
        tick_deadline_ms=15_000,
        tick_interval_ms=0,
        max_ticks=200,
        match_wait_ms=0,
        description="Five-O Poker. Build five 5-card hands and beat your opponent in the most columns.",
    )

    def initial_state(self, seed: int, num_players: int) -> dict:
        if num_players != 2:
            raise ValueError("Five-O Poker requires exactly 2 players.")

        deck = list(new_shuffled_deck(seed, 1))
        players = []
        for seat in range(2):
            # One card dealt face-up to each column to start.
            columns = [[deck.pop(0)] for _ in range(NUM_COLUMNS)]
            players.append({"seat": seat, "columns": columns, "last_action": None})

        return {
            "tick": 0,
            "seed": seed,
            "phase": "placing",  # placing -> done
            "action_on": 0,
            "deck": deck,
            "current_drawn_card": deck.pop(0),  # card the actor must place
            "players": players,
            "history": [],
            "history_delta": [],
            "placement": [],
            "winner": None,
            "showdown_hands": None,
            "winning_columns": None,
        }

    def alive_seats(self, state: dict) -> list[int]:
        return [p["seat"] for p in state["players"]]

    def acting_seats(self, state: dict) -> list[int]:
        if state["action_on"] is None:
            return []
        return [state["action_on"]]

    def view_for(self, state: dict, seat: int) -> dict:
        """Strip the deck and seed; redact the opponent's face-down card."""
        reveal = state["phase"] == "done"
        view_players = []
        for p in state["players"]:
            if p["seat"] == seat or reveal:
                view_players.append({**p})
                continue
            cols = [
                [
                    "??" if idx == HIDDEN_CARD_INDEX else card
                    for idx, card in enumerate(col)
                ]
                for col in p["columns"]
            ]
            view_players.append({**p, "columns": cols})
        view = {k: v for k, v in state.items() if k != "seed"}
        view["deck"] = []
        view["players"] = view_players
        return view

    def delta_view_for(self, state: dict, seat: int) -> dict:
        view = self.view_for(state, seat)
        view.pop("history", None)
        return view

    def journal_view(self, state: dict) -> dict:
        return {k: v for k, v in state.items() if k != "history"}

    def legal_actions(self, state: dict, seat: int) -> list[dict]:
        if state["action_on"] != seat or state["phase"] != "placing":
            return []
        if state["current_drawn_card"] is None:
            return []
        # Pacing rule: a column may take a card only while it is among the
        # shortest columns (keeps all columns within one card of each other)
        # and is not already full.
        p = _seat(state, seat)
        lengths = [len(col) for col in p["columns"]]
        min_len = min(lengths)
        return [
            {"type": "place", "column": idx}
            for idx, length in enumerate(lengths)
            if length == min_len and length < CARDS_PER_COLUMN
        ]

    def is_legal(self, state: dict, seat: int, action: dict) -> bool:
        if state["action_on"] != seat or not isinstance(action, dict):
            return False
        if action.get("type") != "place":
            return False
        return any(
            a["column"] == action.get("column")
            for a in self.legal_actions(state, seat)
        )

    def default_action(self, state: dict, seat: int) -> dict:
        legal = self.legal_actions(state, seat)
        return legal[0] if legal else {}

    def step(self, state: dict, actions: dict[int, dict]) -> StepResult:
        prev_hist_len = len(state.get("history") or [])
        actor = state["action_on"]
        if actor is None:
            new_state = {**state, "tick": state["tick"] + 1, "history_delta": []}
            return StepResult(state=new_state, done=False)

        action = actions.get(actor)
        if action is None or not self.is_legal(state, actor, action):
            action = self.default_action(state, actor)

        new_state = _apply_placement(state, actor, action)

        placed = sum(len(col) for p in new_state["players"] for col in p["columns"])
        if placed == TOTAL_CARDS:
            new_state = _run_showdown(new_state)
            return StepResult(
                state=_bump_tick(_stamp_history_delta(new_state, prev_hist_len)),
                done=True,
                placement=list(new_state["placement"]),
                reason=new_state["result_reason"],
            )

        # Hand off to the other player and draw the next card.
        deck = list(new_state["deck"])
        new_state = {
            **new_state,
            "action_on": 1 - actor,
            "current_drawn_card": deck.pop(0),
            "deck": deck,
        }
        return StepResult(
            state=_bump_tick(_stamp_history_delta(new_state, prev_hist_len)),
            done=False,
        )


# ── module-level helpers ───────────────────────────────────────────────────


def _seat(state: dict, seat: int) -> dict:
    return next(p for p in state["players"] if p["seat"] == seat)


def _bump_tick(state: dict) -> dict:
    return {**state, "tick": state["tick"] + 1}


def _stamp_history_delta(state: dict, prev_len: int) -> dict:
    hist = state.get("history") or []
    return {**state, "history_delta": hist[prev_len:]}


def _apply_placement(state: dict, seat: int, action: dict) -> dict:
    players = [dict(p) for p in state["players"]]
    p = next(pl for pl in players if pl["seat"] == seat)
    cols = [list(col) for col in p["columns"]]
    cols[action["column"]].append(state["current_drawn_card"])
    p["columns"] = cols
    p["last_action"] = action
    history = list(state.get("history") or [])
    history.append({"seat": seat, "action": action})
    return {**state, "players": players, "history": history}


def _run_showdown(state: dict) -> dict:
    """Compare the two players' five columns head-to-head. The player who wins
    the most columns wins the game; equal columns won is a draw."""
    players = [dict(p) for p in state["players"]]
    p0, p1 = players[0], players[1]

    p0_hands = [rank(p0["columns"][i], []) for i in range(NUM_COLUMNS)]
    p1_hands = [rank(p1["columns"][i], []) for i in range(NUM_COLUMNS)]
    showdown_hands = {
        "0": [str(h) for h in p0_hands],
        "1": [str(h) for h in p1_hands],
    }

    cols0: list[int] = []
    cols1: list[int] = []
    for i in range(NUM_COLUMNS):
        if p0_hands[i] > p1_hands[i]:
            cols0.append(i)
        elif p1_hands[i] > p0_hands[i]:
            cols1.append(i)
        # Tied columns count for neither player.
    winning_columns = {"0": cols0, "1": cols1}

    if len(cols0) > len(cols1):
        winner, placement, reason = 0, [0, 1], "showdown"
    elif len(cols1) > len(cols0):
        winner, placement, reason = 1, [1, 0], "showdown"
    else:
        winner, placement, reason = -1, [0, 1], "draw"

    return {
        **state,
        "players": players,
        "phase": "done",
        "action_on": None,
        "winner": winner,
        "placement": placement,
        "result_reason": reason,
        "showdown_hands": showdown_hands,
        "winning_columns": winning_columns,
    }
