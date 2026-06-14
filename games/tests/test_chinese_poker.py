"""Tests for Chinese Poker (Five-O Rules) game engine."""

from __future__ import annotations

from vibewarz_games.chinese_poker.game import (
    CARDS_PER_COLUMN,
    NUM_COLUMNS,
    ChinesePoker,
)


def _play_to_end(cp: ChinesePoker, s: dict):
    """Drive a full game with default placements; return the final StepResult."""
    res = None
    for _ in range(cp.meta.max_ticks):
        actor = s["action_on"]
        res = cp.step(s, {actor: cp.default_action(s, actor)})
        s = res.state
        if res.done:
            return res
    raise AssertionError("game did not finish within max_ticks")


def test_initial_state():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)
    assert s["phase"] == "placing"
    assert s["action_on"] == 0
    assert len(s["players"]) == 2
    for p in s["players"]:
        assert len(p["columns"]) == NUM_COLUMNS
        # Each column starts with 1 card dealt.
        for col in p["columns"]:
            assert len(col) == 1
    assert s["current_drawn_card"] is not None


def test_placing_legal_actions_and_step():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)
    actor = s["action_on"]
    legal = cp.legal_actions(s, actor)
    # All five columns are length 1, so all are legal placements.
    assert len(legal) == NUM_COLUMNS
    assert all(a["type"] == "place" for a in legal)

    s2 = cp.step(s, {actor: {"type": "place", "column": 0}}).state
    p_after = next(p for p in s2["players"] if p["seat"] == actor)
    assert len(p_after["columns"][0]) == 2
    for col in p_after["columns"][1:]:
        assert len(col) == 1
    # Players alternate placements.
    assert s2["action_on"] == 1 - actor


def test_pacing_rule():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)
    s = cp.step(s, {0: {"type": "place", "column": 0}}).state  # -> seat 1
    s = cp.step(s, {1: {"type": "place", "column": 0}}).state  # -> back to seat 0

    # Seat 0's column 0 now has 2 cards; the rest have 1. The pacing rule
    # forces the next card into one of the still-shortest columns (1..4).
    assert s["action_on"] == 0
    columns = {a["column"] for a in cp.legal_actions(s, 0)}
    assert 0 not in columns
    assert columns == {1, 2, 3, 4}


def test_view_redacts_face_down_card():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)
    # Fill every column to 4 cards (indices 0..3) for both players.
    for _ in range(30):
        actor = s["action_on"]
        s = cp.step(s, {actor: cp.default_action(s, actor)}).state

    v0 = cp.view_for(s, 0)
    p0 = next(p for p in v0["players"] if p["seat"] == 0)
    p1 = next(p for p in v0["players"] if p["seat"] == 1)

    # Seat 0 sees their own face-down card; the opponent's is redacted.
    for col in p0["columns"]:
        if len(col) >= 4:
            assert col[3] != "??"
    for col in p1["columns"]:
        if len(col) >= 4:
            assert col[3] == "??"


def test_full_game_resolves_to_a_winner():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)
    res = _play_to_end(cp, s)
    final = res.state

    assert res.done is True
    assert final["phase"] == "done"
    assert final["action_on"] is None
    # Both boards are fully built.
    for p in final["players"]:
        for col in p["columns"]:
            assert len(col) == CARDS_PER_COLUMN
    # Showdown produced per-column results and a placement.
    assert final["showdown_hands"] is not None
    assert final["winning_columns"] is not None
    assert sorted(res.placement) == [0, 1]
    assert final["winner"] in (0, 1, -1)
    won0 = len(final["winning_columns"]["0"])
    won1 = len(final["winning_columns"]["1"])
    if final["winner"] == 0:
        assert won0 > won1 and res.placement[0] == 0
    elif final["winner"] == 1:
        assert won1 > won0 and res.placement[0] == 1
    else:
        assert won0 == won1  # draw


def test_showdown_reveals_opponent_cards():
    cp = ChinesePoker()
    s = cp.initial_state(seed=7, num_players=2)
    final = _play_to_end(cp, s).state
    # At showdown nothing is redacted, for either seat's view.
    for viewer in (0, 1):
        view = cp.view_for(final, viewer)
        for p in view["players"]:
            for col in p["columns"]:
                assert "??" not in col
