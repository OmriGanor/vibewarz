"""Chinese Poker (Five-O Rules) game implementation.

A 2-player game where players build five 5-card hands (columns) simultaneously.
1. Deal: 5 cards dealt face-up (1 per column).
2. Pacing: Draw 1 card at a time, place it in any column. Every column must have the same number of cards before a player can place a card in the next level.
3. Visibility: Card 4 is dealt face-down (redacted in views). Card 5 is face-up.
4. Showdown: Beat opponent in 3/5 or more columns to win. Winning all 5 is a "Five-O" scoop win.
"""

from __future__ import annotations

import random
from typing import Final

from .._core.base import Game, GameMeta, StepResult
from .._core.registry import register
from ..poker.betting import new_shuffled_deck
from ..poker.hand_eval import rank, best_seats

STARTING_STACK: Final = 1000
BLIND_LEVELS: Final = (10, 20)  # simple SB and BB for betting stage

@register
class ChinesePoker(Game):
    meta = GameMeta(
        id="chinese_poker",
        display_name="Chinese Poker",
        min_players=2,
        max_players=2,
        tick_deadline_ms=15_000,
        tick_interval_ms=0,
        max_ticks=5_000,
        match_wait_ms=0,
        description="Chinese Poker with Five-O Rules. Build 5 hands simultaneously and beat your opponent in 3/5 rows.",
    )

    def initial_state(self, seed: int, num_players: int) -> dict:
        if num_players != 2:
            raise ValueError("Chinese Poker (Five-O) requires exactly 2 players.")

        players = []
        for seat in range(2):
            players.append({
                "seat": seat,
                "stack": STARTING_STACK,
                "in_tournament": True,
                "in_hand": True,
                # 5 columns, each initially holding 1 card (first deal) or empty before first deal.
                # In Five-O, deal starts with 5 cards dealt face-up (1 per column)
                "columns": [[] for _ in range(5)],
                "folded": False,
                "all_in": False,
                "committed_round": 0,
                "committed_hand": 0,
                "last_action": None,
            })

        state = {
            "tick": 0,
            "seed": seed,
            "hand_number": 0,
            "phase": "placing",  # placing -> betting -> showdown -> hand_complete -> done
            "button": 0,
            "deck": [],
            "pot": 0,
            "current_bet": 0,
            "min_raise": BLIND_LEVELS[1],
            "action_on": 0, # Seat 0 acts first to place
            "acted_this_round": [],
            "players": players,
            "history": [],
            "history_delta": [],
            "placement": [],
            "pot_distribution": None,
            "showdown_hands": None,  # evaluated strength text for each seat and column
            "current_drawn_card": None, # The card currently drawn that the actor needs to place
        }
        return _start_new_hand(state)

    def alive_seats(self, state: dict) -> list[int]:
        return [p["seat"] for p in state["players"] if p["in_tournament"]]

    def acting_seats(self, state: dict) -> list[int]:
        if state["action_on"] is None:
            return []
        return [state["action_on"]]

    def view_for(self, state: dict, seat: int) -> dict:
        """Strip remaining deck, seed, and other players' face-down cards (index 3)."""
        view_players = []
        is_showdown = state["phase"] in ("showdown", "hand_complete", "done")
        for p in state["players"]:
            cols = []
            for col in p["columns"]:
                # Card at index 4 (5th card, last round) is face-down.
                visible_col = []
                for idx, card in enumerate(col):
                    if idx == 4 and p["seat"] != seat and not is_showdown:
                        visible_col.append("??")
                    else:
                        visible_col.append(card)
                cols.append(visible_col)

            view_players.append({
                **p,
                "columns": cols,
            })
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
        if state["action_on"] != seat:
            return []

        p = next(pl for pl in state["players"] if pl["seat"] == seat)
        if state["phase"] == "placing":
            if state["current_drawn_card"] is None:
                return []
            # In Five-O, players alternate placing. The pacing rule states:
            # "players must place one card on each of their columns before continuing to build the other columns."
            # "The columns must be equal in each round."
            # Therefore, we check the column lengths of this player. They must all be equal to either min_len or min_len + 1.
            # To be precise: a column can accept a card if its length is equal to the minimum length of columns.
            lengths = [len(col) for col in p["columns"]]
            min_len = min(lengths)
            actions = []
            for col_idx, length in enumerate(lengths):
                if length == min_len and length < 5:
                    actions.append({"type": "place", "column": col_idx})
            return actions

        elif state["phase"] == "betting":
            if p["all_in"]:
                return []
            to_call = state["current_bet"] - p["committed_round"]
            actions = [{"type": "fold"}]
            if to_call <= 0:
                actions.append({"type": "check"})
            else:
                actions.append({"type": "call"})
            
            # Raise options
            full_min = state["current_bet"] + state["min_raise"]
            if p["stack"] + p["committed_round"] > state["current_bet"]:
                if p["stack"] + p["committed_round"] >= full_min:
                    actions.append({"type": "raise", "to": full_min})
                    if p["stack"] + p["committed_round"] > full_min:
                        actions.append({"type": "raise", "to": p["stack"] + p["committed_round"]})
                else:
                    # short stack all-in
                    actions.append({"type": "raise", "to": p["stack"] + p["committed_round"]})
            return actions

        elif state["phase"] == "hand_complete":
            return [{"type": "ready"}]

        return []

    def is_legal(self, state: dict, seat: int, action: dict) -> bool:
        legal = self.legal_actions(state, seat)
        if not legal:
            return False
        for a in legal:
            if a["type"] == action.get("type"):
                if a["type"] == "place" and a["column"] == action.get("column"):
                    return True
                if a["type"] in ("fold", "check", "call", "ready"):
                    return True
                if a["type"] == "raise" and a["to"] == action.get("to"):
                    return True
        return False

    def default_action(self, state: dict, seat: int) -> dict:
        legal = self.legal_actions(state, seat)
        if not legal:
            return {}
        if state["phase"] in ("placing", "hand_complete"):
            return legal[0]
        else:
            p = next(pl for pl in state["players"] if pl["seat"] == seat)
            if state["current_bet"] <= p["committed_round"]:
                return {"type": "check"}
            return {"type": "fold"}

    def step(self, state: dict, actions: dict[int, dict]) -> StepResult:
        prev_hist_len = len(state.get("history") or [])
        actor = state["action_on"]
        if actor is None:
            new_state = {**state, "tick": state["tick"] + 1, "history_delta": []}
            return StepResult(state=new_state, done=False)

        action = actions.get(actor)
        if action is None or not self.is_legal(state, actor, action):
            action = self.default_action(state, actor)

        new_state = _apply_action(state, actor, action)
        eliminated: list[int] = []

        # Loop to advance states
        while True:
            # Check if hand resolved uncontested
            in_hand = [p for p in new_state["players"] if p["in_hand"]]
            if len(in_hand) == 1:
                # Contestant won uncontested
                new_state = _award_uncontested(new_state)
                new_state, busted = _settle_busts(new_state)
                eliminated.extend(busted)
                if _tournament_done(new_state):
                    new_state = _finalize_tournament(new_state)
                    return StepResult(
                        state=_bump_tick(_stamp_history_delta(new_state, prev_hist_len)),
                        done=True,
                        placement=list(new_state["placement"]),
                        reason="elimination",
                        eliminated_this_tick=tuple(eliminated),
                    )
                # Wait for player to ready up
                new_state["action_on"] = 0
                break

            if new_state["phase"] == "placing":
                # Check if placing phase is done (both players have 25 cards total)
                tot_cards = sum(len(col) for p in new_state["players"] for col in p["columns"])
                if tot_cards == 50:
                    # Move to betting round!
                    new_state["phase"] = "betting"
                    new_state["current_drawn_card"] = None
                    # First actor is button left, which is SB (non-button in 2p)
                    new_state["action_on"] = 1 - new_state["button"]
                    new_state["acted_this_round"] = []
                    # Force post blinds
                    new_state = _post_blinds(new_state)
                    # Next to act depends on action after post blinds
                    new_state["action_on"] = _next_to_act_betting(new_state)
                else:
                    # Keep placing. Alternate actions.
                    # In Five-O placing, players alternate placement.
                    next_placer = 1 - actor
                    new_state["action_on"] = next_placer
                    # Draw a new card if the deck has cards
                    if len(new_state["deck"]) > 0:
                        new_state["current_drawn_card"] = new_state["deck"].pop(0)
                break

            elif new_state["phase"] == "betting":
                if _is_betting_complete(new_state):
                    # Proceed to showdown
                    new_state = _run_showdown(new_state)
                    new_state, busted = _settle_busts(new_state)
                    eliminated.extend(busted)
                    if _tournament_done(new_state):
                        new_state = _finalize_tournament(new_state)
                        return StepResult(
                            state=_bump_tick(_stamp_history_delta(new_state, prev_hist_len)),
                            done=True,
                            placement=list(new_state["placement"]),
                            reason="elimination",
                            eliminated_this_tick=tuple(eliminated),
                        )
                    # Wait for player to ready up
                    new_state["action_on"] = 0
                    break
                else:
                    new_state["action_on"] = _next_to_act_betting(new_state)
                    break

            elif new_state["phase"] == "hand_complete":
                # Only reachable if action was 'ready' (processed by _apply_action)
                new_state = _start_new_hand(new_state)
                # Loop will naturally hit 'placing' branch and break
                continue

            else:
                break

        return StepResult(
            state=_bump_tick(_stamp_history_delta(new_state, prev_hist_len)),
            done=False,
            eliminated_this_tick=tuple(eliminated),
        )

# -- State helpers --

def _bump_tick(state: dict) -> dict:
    return {**state, "tick": state["tick"] + 1}

def _stamp_history_delta(state: dict, prev_len: int) -> dict:
    hist = state.get("history") or []
    return {**state, "history_delta": hist[prev_len:]}

def _tournament_done(state: dict) -> bool:
    return len([p for p in state["players"] if p["in_tournament"]]) <= 1

def _start_new_hand(state: dict) -> dict:
    # Set/Reset hand stats
    players = []
    for p in state["players"]:
        players.append({
            **p,
            "in_hand": bool(p["in_tournament"]),
            "columns": [[] for _ in range(5)],
            "folded": False,
            "all_in": False,
            "committed_round": 0,
            "committed_hand": 0,
            "last_action": None,
        })
    
    state = {
        **state,
        "players": players,
        "pot": 0,
        "current_bet": 0,
        "min_raise": BLIND_LEVELS[1],
        "phase": "placing",
        "showdown_hands": None,
    }

    state["hand_number"] += 1
    # Rotate button
    state["button"] = (state["button"] + 1) % 2

    # Shuffle fresh deck
    deck = list(new_shuffled_deck(state["seed"], state["hand_number"]))

    # Deal 5 cards to each player face-up (1 card per column)
    # Seat 0 gets 5 cards, Seat 1 gets 5 cards
    for seat in (0, 1):
        p = state["players"][seat]
        p["columns"] = [[] for _ in range(5)]
        for col_idx in range(5):
            p["columns"][col_idx].append(deck.pop(0))

    state["deck"] = deck
    # Initial placer is the button (in heads-up, button acts first to place or SB acts first?
    # Standard: let's start with button (Seat button) to place first.
    state["action_on"] = state["button"]
    state["current_drawn_card"] = deck.pop(0)

    return state

def _apply_action(state: dict, seat: int, action: dict) -> dict:
    typ = action["type"]
    players = [dict(p) for p in state["players"]]
    p = next(pl for pl in players if pl["seat"] == seat)
    history = list(state.get("history") or [])
    acted = list(state.get("acted_this_round") or [])
    current_bet = state["current_bet"]
    pot = state["pot"]

    if state["phase"] == "placing":
        if typ == "place":
            col_idx = action["column"]
            p["columns"] = [list(col) for col in p["columns"]]
            p["columns"][col_idx].append(state["current_drawn_card"])
            p["last_action"] = action
    
    elif state["phase"] == "betting":
        p["last_action"] = action
        if typ == "fold":
            p["in_hand"] = False
            p["folded"] = True
        elif typ == "check":
            if seat not in acted:
                acted.append(seat)
        elif typ == "call":
            owe = current_bet - p["committed_round"]
            pay = min(owe, p["stack"])
            p["stack"] -= pay
            p["committed_round"] += pay
            p["committed_hand"] += pay
            if p["stack"] == 0:
                p["all_in"] = True
            if seat not in acted:
                acted.append(seat)
        elif typ == "raise":
            to = action["to"]
            increment = to - p["committed_round"]
            p["stack"] -= increment
            p["committed_round"] = to
            p["committed_hand"] += increment
            if p["stack"] == 0:
                p["all_in"] = True
            current_bet = to
            acted = [seat]  # reset acted tracker for the new bet

    history.append({
        "hand": state["hand_number"],
        "phase": state["phase"],
        "seat": seat,
        "action": action,
    })

    return {
        **state,
        "players": players,
        "current_bet": current_bet,
        "pot": pot,
        "acted_this_round": acted,
        "history": history,
    }

def _post_blinds(state: dict) -> dict:
    # In 2-player poker, SB is button (button posts SB, non-button posts BB)
    button = state["button"]
    sb_seat = button
    bb_seat = 1 - button

    state = _force_post(state, sb_seat, BLIND_LEVELS[0])
    state = _force_post(state, bb_seat, BLIND_LEVELS[1])
    return state

def _force_post(state: dict, seat: int, amount: int) -> dict:
    players = [dict(p) for p in state["players"]]
    p = next(pl for pl in players if pl["seat"] == seat)
    pay = min(amount, p["stack"])
    p["stack"] -= pay
    p["committed_round"] += pay
    p["committed_hand"] += pay
    if p["stack"] == 0:
        p["all_in"] = True
    current_bet = max(state["current_bet"], p["committed_round"])
    return {**state, "players": players, "current_bet": current_bet}

def _next_to_act_betting(state: dict) -> int | None:
    # Check if betting complete
    in_hand = [p for p in state["players"] if p["in_hand"] and not p["all_in"]]
    if len(in_hand) <= 1:
        return None
    
    current_bet = state["current_bet"]
    acted = state["acted_this_round"]
    for p in in_hand:
        if p["committed_round"] < current_bet or p["seat"] not in acted:
            return p["seat"]
    return None

def _is_betting_complete(state: dict) -> bool:
    in_hand = [p for p in state["players"] if p["in_hand"] and not p["all_in"]]
    if len(in_hand) <= 1:
        return True
    current_bet = state["current_bet"]
    acted = state["acted_this_round"]
    return all(p["committed_round"] == current_bet and p["seat"] in acted for p in in_hand)

def _award_uncontested(state: dict) -> dict:
    winner = next(p["seat"] for p in state["players"] if p["in_hand"])
    # collect all committed
    total_pot = state["pot"] + sum(p["committed_round"] for p in state["players"])
    players = [dict(p) for p in state["players"]]
    next(p for p in players if p["seat"] == winner)["stack"] += total_pot
    for p in players:
        p["committed_round"] = 0
        p["committed_hand"] = 0
    return {
        **state,
        "players": players,
        "pot": 0,
        "pot_distribution": [{"seat": winner, "amount": total_pot}],
        "phase": "hand_complete",
    }

def _run_showdown(state: dict) -> dict:
    # Move committed round to pot
    total_pot = state["pot"] + sum(p["committed_round"] for p in state["players"])
    players = [dict(p) for p in state["players"]]
    for p in players:
        p["committed_round"] = 0

    p0 = players[0]
    p1 = players[1]

    # Evaluate all 5 columns for both players
    # Using StandardHighHand evaluator from pokerkit. But pokerkit standard ranking needs 5 cards.
    # Columns in Five-O have exactly 5 cards each.
    p0_hands = []
    p1_hands = []
    for col_idx in range(5):
        # standard pokerkit format for hole cards and board is e.g. rank("AhKhQhJhTh", "")
        p0_hands.append(rank(p0["columns"][col_idx], []))
        p1_hands.append(rank(p1["columns"][col_idx], []))

    showdown_hands = {
        "0": [str(h) for h in p0_hands],
        "1": [str(h) for h in p1_hands],
    }

    # Compare columns head-to-head
    p0_wins = 0
    p1_wins = 0
    winning_cols_0 = []
    winning_cols_1 = []
    for col_idx in range(5):
        h0 = p0_hands[col_idx]
        h1 = p1_hands[col_idx]
        if h0 > h1:
            p0_wins += 1
            winning_cols_0.append(col_idx)
        elif h1 > h0:
            p1_wins += 1
            winning_cols_1.append(col_idx)
        else:
            # Tie on this column: split points? For head-to-head count, tie doesn't count for either.
            pass
            
    winning_columns = {
        "0": winning_cols_0,
        "1": winning_cols_1,
    }

    # Overall hand winner
    if p0_wins > p1_wins:
        winner = 0
    elif p1_wins > p0_wins:
        winner = 1
    else:
        # split pot in case of tie in columns won
        winner = -1
    pot_distribution = []
    if winner != -1:
        winner_p = next(p for p in players if p["seat"] == winner)
        winner_p["stack"] += total_pot
        pot_distribution.append({"seat": winner, "amount": total_pot})
    else:
        share = total_pot // 2
        p0_p = next(p for p in players if p["seat"] == 0)
        p1_p = next(p for p in players if p["seat"] == 1)
        p0_p["stack"] += share
        p1_p["stack"] += total_pot - share
        pot_distribution.append({"seat": 0, "amount": share})
        pot_distribution.append({"seat": 1, "amount": total_pot - share})

    for p in players:
        p["committed_hand"] = 0

    return {
        **state,
        "players": players,
        "pot": 0,
        "pot_distribution": pot_distribution,
        "showdown_hands": showdown_hands,
        "winning_columns": winning_columns,
        "phase": "hand_complete",
    }

def _settle_busts(state: dict) -> tuple[dict, list[int]]:
    players = [dict(p) for p in state["players"]]
    newly_busted: list[int] = []
    placement = list(state["placement"])
    for p in sorted(players, key=lambda pp: pp["seat"]):
        if p["in_tournament"] and p["stack"] <= 0:
            p["in_tournament"] = False
            p["in_hand"] = False
            newly_busted.append(p["seat"])
            if p["seat"] not in placement:
                placement.append(p["seat"])
    state = {**state, "players": players, "placement": placement}
    return state, newly_busted

def _finalize_tournament(state: dict) -> dict:
    placement = list(state["placement"])
    survivors = sorted(
        (p["seat"] for p in state["players"] if p["in_tournament"]),
    )
    for seat in survivors:
        if seat not in placement:
            placement.append(seat)
    final = list(reversed(placement))
    return {**state, "placement": final, "phase": "done", "action_on": None}
