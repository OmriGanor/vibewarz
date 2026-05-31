"""Vibelords engine tests."""

from __future__ import annotations

import json

import pytest
from vibewarz_games import GAMES
from vibewarz_games.vibelords import units as U
from vibewarz_games.vibelords.game import (
    BASE_HP,
    LANE_LENGTH,
    MAX_TICKS,
    PASSIVE_GOLD,
    SPECIAL_CD,
    Vibelords,
)


@pytest.fixture
def vibelords() -> Vibelords:
    return Vibelords()


def _noop2() -> dict[int, dict]:
    return {0: {"type": "noop"}, 1: {"type": "noop"}}


def _unit(uid: str, owner: int, unit: str, x: float, age: int = 0) -> dict:
    st = U.unit_stats(unit, age)
    return {
        "id": uid,
        "owner": owner,
        "unit": unit,
        "age": age,
        "x": float(x),
        "hp": float(st["hp"]),
        "max_hp": st["hp"],
        "atk_cd": 0,
    }


def _duel_winner(vibelords: Vibelords, u0: str, u1: str, x0: float, x1: float) -> int | None:
    """Place one unit per side, step (both passing) until one dies; return the
    surviving owner (or None on a draw/timeout)."""
    state = vibelords.initial_state(seed=1, num_players=2)
    state["units"] = [_unit("uA", 0, u0, x0), _unit("uB", 1, u1, x1)]
    state["next_unit_id"] = 2
    for _ in range(400):
        res = vibelords.step(state, _noop2())
        state = res.state
        owners = {u["owner"] for u in state["units"]}
        if len(owners) <= 1:
            return next(iter(owners)) if owners else None
        if res.done:
            break
    return None


# ── registration & shape ────────────────────────────────────────────────────


def test_registered_in_global_registry() -> None:
    assert "vibelords" in GAMES
    assert GAMES["vibelords"] is Vibelords


def test_initial_state_shape(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=42, num_players=2)
    assert state["tick"] == 0
    assert state["lane"] == {"length": LANE_LENGTH}
    assert state["units"] == []
    assert state["placement"] == []
    assert len(state["players"]) == 2
    assert len(state["bases"]) == 2
    for seat, b in enumerate(state["bases"]):
        assert b["seat"] == seat
        assert b["hp"] == BASE_HP
    for seat, p in enumerate(state["players"]):
        assert p["seat"] == seat
        assert p["age"] == 0
        assert p["queue"] == []
    assert vibelords.alive_seats(state) == [0, 1]


def test_rejects_non_two_player(vibelords: Vibelords) -> None:
    with pytest.raises(ValueError):
        vibelords.initial_state(seed=1, num_players=3)


# ── action contract ──────────────────────────────────────────────────────────


def test_legal_actions_all_pass_is_legal(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=3, num_players=2)
    # exercise a richer mid-game state too
    for _ in range(120):
        actions = {
            s: vibelords.legal_actions(state, s)[-1] for s in vibelords.acting_seats(state)
        }
        state = vibelords.step(state, actions).state
    for seat in (0, 1):
        for action in vibelords.legal_actions(state, seat):
            assert vibelords.is_legal(state, seat, action), action
        assert vibelords.is_legal(state, seat, vibelords.default_action(state, seat))


def test_is_legal_rejects_garbage(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=3, num_players=2)
    assert not vibelords.is_legal(state, 0, {"type": "teleport"})
    assert not vibelords.is_legal(state, 0, {"type": "build", "unit": "dragon"})
    assert not vibelords.is_legal(state, 0, "noop")  # type: ignore[arg-type]


def test_unaffordable_build_is_noop_not_illegal(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=3, num_players=2)
    state["players"][0]["gold"] = 0.0
    action = {"type": "build", "unit": "pike"}
    assert vibelords.is_legal(state, 0, action)  # stays legal
    res = vibelords.step(state, {0: action, 1: {"type": "noop"}})
    assert res.state["players"][0]["queue"] == []  # but did nothing


# ── determinism & redaction ──────────────────────────────────────────────────


def test_step_is_deterministic(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=7, num_players=2)
    actions = {0: {"type": "build", "unit": "pike"}, 1: {"type": "build", "unit": "archer"}}
    a = vibelords.step(state, actions)
    b = vibelords.step(state, actions)
    assert json.dumps(a.state, sort_keys=True) == json.dumps(b.state, sort_keys=True)


def test_view_for_hides_seed_and_opponent_queue(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=7, num_players=2)
    state["players"][0]["queue"].append({"unit": "pike", "age": 0, "ready_tick": 9})
    state["players"][1]["queue"].append({"unit": "archer", "age": 0, "ready_tick": 9})
    v0 = vibelords.view_for(state, 0)
    assert "seed" not in v0
    assert v0["players"][0]["queue"] == state["players"][0]["queue"]  # own queue kept
    assert v0["players"][1]["queue"] == []  # opponent queue hidden
    # public info still visible
    assert v0["players"][1]["gold"] == state["players"][1]["gold"]
    assert v0["bases"] == state["bases"]


def test_state_is_json_roundtrippable(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=7, num_players=2)
    for _ in range(50):
        actions = {0: {"type": "build", "unit": "cavalry"}, 1: {"type": "noop"}}
        state = vibelords.step(state, actions).state
    assert json.loads(json.dumps(state)) == json.loads(json.dumps(state))


# ── economy & queue mechanics ────────────────────────────────────────────────


def test_passive_income_accrues(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=1, num_players=2)
    g0 = state["players"][0]["gold"]
    state = vibelords.step(state, _noop2()).state
    assert state["players"][0]["gold"] == pytest.approx(g0 + PASSIVE_GOLD)


def test_build_queues_then_hatches(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=1, num_players=2)
    bt = U.unit_stats("pike", 0)["build_ticks"]
    res = vibelords.step(state, {0: {"type": "build", "unit": "pike"}, 1: {"type": "noop"}})
    state = res.state
    assert len(state["players"][0]["queue"]) == 1
    assert state["units"] == []  # not deployed yet (hidden build time)
    # step until it hatches
    mine: list[dict] = []
    for _ in range(bt + 2):
        state = vibelords.step(state, _noop2()).state
        mine = [u for u in state["units"] if u["owner"] == 0]
        if mine:
            break
    assert len(mine) == 1
    assert mine[0]["unit"] == "pike"
    # deploys at its own base edge (x=0), then takes its first march step
    assert mine[0]["x"] <= U.unit_stats("pike", 0)["speed"]


def test_advance_age_consumes_xp(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=1, num_players=2)
    state["players"][0]["xp"] = U.age_up_cost(0) + 5
    res = vibelords.step(state, {0: {"type": "advance_age"}, 1: {"type": "noop"}})
    assert res.state["players"][0]["age"] == 1


def test_special_sets_cooldown_and_hits_enemy_units(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=1, num_players=2)
    # enemy (seat 1) unit sitting in seat 0's defensive half
    state["units"] = [_unit("e", 1, "pike", LANE_LENGTH * 0.25)]
    state["next_unit_id"] = 1
    hp_before = state["units"][0]["hp"]
    res = vibelords.step(state, {0: {"type": "special"}, 1: {"type": "noop"}})
    assert res.state["players"][0]["special_cd"] == SPECIAL_CD
    survivor = [u for u in res.state["units"] if u["owner"] == 1]
    # took airstrike damage (or died)
    assert (not survivor) or survivor[0]["hp"] < hp_before
    assert any(fx["kind"] == "airstrike" for fx in res.state["fx"])


# ── rock-paper-scissors combat ───────────────────────────────────────────────


def test_counter_map_is_a_cycle() -> None:
    assert U.COUNTERS == {"pike": "cavalry", "cavalry": "archer", "archer": "pike"}
    assert U.damage_multiplier("pike", "cavalry") == U.ADVANTAGE_MULT
    assert U.damage_multiplier("cavalry", "pike") == 1.0


def test_pike_beats_cavalry(vibelords: Vibelords) -> None:
    assert _duel_winner(vibelords, "pike", "cavalry", 500, 510) == 0


def test_cavalry_beats_archer(vibelords: Vibelords) -> None:
    assert _duel_winner(vibelords, "cavalry", "archer", 500, 520) == 1 - 1  # owner 0


def test_archer_beats_pike(vibelords: Vibelords) -> None:
    assert _duel_winner(vibelords, "archer", "pike", 420, 480) == 0


def test_higher_age_unit_beats_lower(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=1, num_players=2)
    state["units"] = [_unit("a", 0, "pike", 500, age=1), _unit("b", 1, "pike", 510, age=0)]
    state["next_unit_id"] = 2
    winner = None
    for _ in range(400):
        res = vibelords.step(state, _noop2())
        state = res.state
        owners = {u["owner"] for u in state["units"]}
        if len(owners) <= 1:
            winner = next(iter(owners)) if owners else None
            break
    assert winner == 0  # the age-1 pike


# ── match convergence ────────────────────────────────────────────────────────


def test_rush_destroys_base(vibelords: Vibelords) -> None:
    """A one-sided builder eventually razes the idle opponent's base."""
    state = vibelords.initial_state(seed=5, num_players=2)
    res = None
    for _ in range(MAX_TICKS):
        a0 = vibelords.legal_actions(state, 0)
        # seat 0 builds whatever it can afford, else noop; seat 1 idles
        build = next((x for x in a0 if x["type"] == "build"), {"type": "noop"})
        res = vibelords.step(state, {0: build, 1: {"type": "noop"}})
        state = res.state
        if res.done:
            break
    assert res is not None and res.done
    assert res.reason == "base_destroyed"
    assert res.placement[0] == 0  # the aggressor wins
    assert state["bases"][1]["hp"] <= 0


def test_passive_match_times_out_with_ranking(vibelords: Vibelords) -> None:
    state = vibelords.initial_state(seed=9, num_players=2)
    res = None
    for _ in range(MAX_TICKS + 5):
        res = vibelords.step(state, _noop2())
        state = res.state
        if res.done:
            break
    assert res is not None and res.done
    assert res.reason == "timeout"
    assert sorted(res.placement) == [0, 1]
    assert state["tick"] == MAX_TICKS
