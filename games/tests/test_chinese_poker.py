"""Tests for Chinese Poker (Five-O Rules) game engine."""

from __future__ import annotations

import pytest
from vibewarz_games.chinese_poker.game import ChinesePoker

def test_initial_state():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)
    assert s["phase"] == "placing"
    assert s["hand_number"] == 1
    assert len(s["players"]) == 2
    for p in s["players"]:
        assert len(p["columns"]) == 5
        # Each column starts with 1 card dealt
        for col in p["columns"]:
            assert len(col) == 1
    assert s["current_drawn_card"] is not None

def test_placing_legal_actions_and_step():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)
    actor = s["action_on"]
    legal = cp.legal_actions(s, actor)
    # 5 legal columns to place initially since all columns have length 1
    assert len(legal) == 5
    assert all(a["type"] == "place" for a in legal)

    # Place in column 0
    action = {"type": "place", "column": 0}
    res = cp.step(s, {actor: action})
    s2 = res.state
    # Actor's column 0 should now have 2 cards
    p_after = next(p for p in s2["players"] if p["seat"] == actor)
    assert len(p_after["columns"][0]) == 2
    # All other columns should still have 1 card
    for col in p_after["columns"][1:]:
        assert len(col) == 1

    # Now the other player must act (alternate placing)
    assert s2["action_on"] == 1 - actor

def test_pacing_rule():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)
    
    # Place card 2 in column 0 for player 0
    s = cp.step(s, {0: {"type": "place", "column": 0}}).state
    # Place card 2 in column 0 for player 1
    s = cp.step(s, {1: {"type": "place", "column": 0}}).state

    print("s['action_on']:", s["action_on"])
    print("s['current_drawn_card']:", s["current_drawn_card"])
    print("player 0 columns:", s["players"][0]["columns"])
    # Now the other player acts. s['action_on'] is 1. Player 1 already placed in col 0.
    # Player 1's columns: col 0 has length 2, others have length 1.
    # Player 1's legal actions should be cols 1..4.
    legal = cp.legal_actions(s, 1)
    columns = [a["column"] for a in legal]
    assert 0 not in columns
    assert set(columns) == {1, 2, 3, 4}

def test_betting_and_showdown():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)

    # Fast forward placing phase (50 placements total)
    for _ in range(40): # 10 cards initially dealt, 40 remaining to place
        actor = s["action_on"]
        legal = cp.legal_actions(s, actor)
        action = legal[0]
        s = cp.step(s, {actor: action}).state

    # Phase should now be betting
    assert s["phase"] == "betting"
    # Both players' columns must be fully populated (5 cards each)
    for p in s["players"]:
        for col in p["columns"]:
            assert len(col) == 5

    # Check/Check to trigger showdown
    actor = s["action_on"]
    s = cp.step(s, {actor: {"type": "check"}}).state
    actor = s["action_on"]
    res = cp.step(s, {actor: {"type": "check"}})
    s = res.state

    # Should conclude the hand and prepare next hand
    assert s["phase"] == "placing"
    assert s["hand_number"] == 2
    assert s["pot_distribution"] is not None

def test_view_redacts_card_4():
    cp = ChinesePoker()
    s = cp.initial_state(seed=42, num_players=2)

    # Place up to 3 cards in each column (index 0, 1, 2)
    # Total cards placed: 20 (so index 0, 1, 2 populated for all columns)
    # Then place card 4 (index 3), which is face-down
    for _ in range(30):
        actor = s["action_on"]
        legal = cp.legal_actions(s, actor)
        s = cp.step(s, {actor: legal[0]}).state

    # Both players have 4 cards in some columns
    # Let's inspect the view for player 0
    v0 = cp.view_for(s, 0)
    p0 = next(p for p in v0["players"] if p["seat"] == 0)
    p1 = next(p for p in v0["players"] if p["seat"] == 1)

    # For player 0 themselves, index 3 should be clear/visible
    # For player 1, index 3 of columns with length >= 4 should be "??"
    for col in p0["columns"]:
        if len(col) >= 4:
            assert col[3] != "??"
    for col in p1["columns"]:
        if len(col) >= 4:
            assert col[3] == "??"
