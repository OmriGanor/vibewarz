"""Long-match invariants for the Curve engine.

The bug class this file exists to catch: the engine kills a player
with no obstacle near where they were moving. The canonical instance
was a floating-point false-positive in `_segments_intersect` where
two collinear-but-disjoint segments (bounding boxes 23 units apart)
were mistakenly reported as intersecting; a 450-tick human curve
match died on the final tick for no physical reason (replay
m_17eb7f9d0a3d46e3 in prod).

The unit tests in `test_curve.py` pin the specific 4-point case. This
file is the broader insurance: it drives full matches under scripted
turn policies and checks an invariant after every step. Any future
collision-detection regression that kills players without a nearby
obstacle will fail this test.

Invariant
=========

For every elimination event, the dying seat's *proposed* motion
segment for that tick (from their pre-step head along their action's
heading, by `_speed_for(player)` units) must come within
`SPEED + ε` of at least one of:

  * the arena boundary in the direction of motion (wall crash);
  * a point of any other seat's authoritative trail (other-trail crash);
  * a point of the dying seat's own trail, excluding the last
    `SELF_CLIP_IMMUNE_SEGMENTS` segments (self-trail crash);
  * another seat's *proposed* head this same tick (head-on).

If no obstacle is within reach, the elimination was a false positive
and the assertion fails with a descriptive message.
"""

from __future__ import annotations

import math
import random

import pytest
from vibewarz_games.curve.game import (
    ARENA_H,
    ARENA_W,
    SELF_CLIP_IMMUNE_SEGMENTS,
    SLOW_FACTOR,
    SPEED,
    SPEED_BOOST_FACTOR,
    TURN_RATE_DEG,
    Curve,
)

# Slack for the "near a real obstacle" check. The engine's collision
# happens when the motion *segment* crosses an obstacle segment, so the
# obstacle is at most SPEED away from the start head. We add a small
# epsilon to absorb the same floating-point noise the AABB prefilter was
# introduced to defeat — distance-to-segment math has similar precision
# limits, just less catastrophically. A real false positive (the bug we
# fixed) is 23 units off, far outside this tolerance.
_OBSTACLE_REACH_SLACK = 0.5
_OBSTACLE_REACH = SPEED * SPEED_BOOST_FACTOR + _OBSTACLE_REACH_SLACK


# ─── action-policy generators ───────────────────────────────────────────────


def _policy_straight_only(rng: random.Random, tick: int, seat: int) -> str:
    """Baseline: every seat goes STRAIGHT every tick. Most seats die at
    walls within ~100 ticks; useful as a control that the invariant
    doesn't fire on legit wall crashes."""
    return "STRAIGHT"


def _policy_zigzag(rng: random.Random, tick: int, seat: int) -> str:
    """Reproduces the m_17eb7f9d0a3d46e3 shape: a STRAIGHT run, a short
    LEFT turn burst, another STRAIGHT run at the new heading, then
    RIGHT, repeat. Each "STRAIGHT after a turn" segment is collinear
    with itself for many ticks, generating exactly the configurations
    that trapped the pre-fix _segments_intersect."""
    # 26-tick cycle, per-seat phase offset so seats don't sync.
    phase = (tick + seat * 7) % 26
    if phase < 10:
        return "STRAIGHT"
    if phase < 16:
        return "LEFT"
    if phase < 20:
        return "STRAIGHT"
    return "RIGHT"


def _policy_spiral(rng: random.Random, tick: int, seat: int) -> str:
    """Constant LEFT — each seat traces an inward spiral. The spiral
    closes onto itself, exercising the legitimate self-trail collision
    path heavily. Useful for ensuring the prefilter didn't accidentally
    suppress real trail crashes."""
    return "LEFT"


def _policy_random_walk(rng: random.Random, tick: int, seat: int) -> str:
    """Deterministic from the rng — broad coverage of action sequences
    without sticking to a fixed pattern. The rng is seeded once per test
    invocation, so the test stays reproducible."""
    return rng.choice(("STRAIGHT", "STRAIGHT", "LEFT", "RIGHT"))


_POLICIES = {
    "straight_only": _policy_straight_only,
    "zigzag": _policy_zigzag,
    "spiral": _policy_spiral,
    "random_walk": _policy_random_walk,
}


# ─── geometry helpers (only used by the invariant assertion) ────────────────


def _distance_point_to_segment(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    """Minimum distance from point (px, py) to segment (ax, ay)→(bx, by)."""
    dx, dy = bx - ax, by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def _distance_between_segments(
    a0: tuple[float, float],
    a1: tuple[float, float],
    b0: tuple[float, float],
    b1: tuple[float, float],
) -> float:
    """Minimum distance between two segments (assuming they don't
    intersect — we use this only to test "did segment A come close
    enough to ANY of these segments to count as an obstacle")."""
    return min(
        _distance_point_to_segment(a0[0], a0[1], b0[0], b0[1], b1[0], b1[1]),
        _distance_point_to_segment(a1[0], a1[1], b0[0], b0[1], b1[0], b1[1]),
        _distance_point_to_segment(b0[0], b0[1], a0[0], a0[1], a1[0], a1[1]),
        _distance_point_to_segment(b1[0], b1[1], a0[0], a0[1], a1[0], a1[1]),
    )


def _proposed_head(
    pre_state: dict, seat: int, action: dict, all_effects: dict[int, dict]
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """Replicate the engine's proposed-motion computation for a seat so
    the invariant can ask "where would they have moved this tick?".
    Returns ((x0, y0), (x1, y1)) or None if the seat wasn't moving."""
    p = next(pl for pl in pre_state["players"] if pl["seat"] == seat)
    if not p["alive"]:
        return None
    turn = (action or {}).get("turn", "STRAIGHT")
    new_heading = p["heading_deg"]
    if turn == "LEFT":
        new_heading -= TURN_RATE_DEG
    elif turn == "RIGHT":
        new_heading += TURN_RATE_DEG
    new_heading %= 360.0
    effects = all_effects[seat]
    speed = SPEED
    if "speed" in effects:
        speed *= SPEED_BOOST_FACTOR
    slow_others = any(
        sid != seat and "slow" in eff for sid, eff in all_effects.items()
    )
    if slow_others and "slow" not in effects:
        speed *= SLOW_FACTOR
    rad = math.radians(new_heading)
    return (
        (p["x"], p["y"]),
        (p["x"] + speed * math.cos(rad), p["y"] + speed * math.sin(rad)),
    )


def _decayed_effects(pre_state: dict) -> dict[int, dict]:
    """Replicate the engine's tick-1 effect decay so we read the same
    `effects` the engine used when computing the step's speeds."""
    out: dict[int, dict] = {}
    for p in pre_state["players"]:
        eff = dict(p.get("effects") or {})
        decayed = {k: r - 1 for k, r in eff.items() if r - 1 > 0}
        out[p["seat"]] = decayed
    return out


def _assert_elimination_explainable(
    pre_state: dict,
    dying_seat: int,
    actions: dict[int, dict],
    policy_name: str,
    tick_no: int,
) -> None:
    """Verify the engine's death decision against an independent
    obstacle-distance check. Fails with a descriptive message that
    surfaces enough state to reproduce the configuration in isolation
    (so a future failure points straight at a unit test."""

    effects = _decayed_effects(pre_state)
    motion = _proposed_head(pre_state, dying_seat, actions.get(dying_seat) or {}, effects)
    if motion is None:
        return  # already dead — engine shouldn't be eliminating it again
    (x0, y0), (x1, y1) = motion

    # 1) Wall crash — proposed head outside the arena.
    if x1 < 0.0 or x1 > ARENA_W or y1 < 0.0 or y1 > ARENA_H:
        return

    # 2) Trail crashes (own + others). Distance from the motion segment
    #    to *any* candidate trail segment must be ≤ reach.
    best_obstacle: tuple[float, str] | None = None

    def _consider(label: str, dist: float) -> None:
        nonlocal best_obstacle
        if best_obstacle is None or dist < best_obstacle[0]:
            best_obstacle = (dist, label)

    motion_p0 = (x0, y0)
    motion_p1 = (x1, y1)
    for other_seat, trail in enumerate(pre_state["trails"]):
        if not trail:
            continue
        relevant = (
            trail[:-SELF_CLIP_IMMUNE_SEGMENTS]
            if other_seat == dying_seat
            else trail
        )
        for i in range(len(relevant) - 1):
            d = _distance_between_segments(
                motion_p0,
                motion_p1,
                tuple(relevant[i]),
                tuple(relevant[i + 1]),
            )
            _consider(f"seat {other_seat} trail segment {i}→{i+1}", d)
            if d <= _OBSTACLE_REACH:
                return

    # 3) Head-on with another seat's proposed head this same tick.
    for other_seat in range(len(pre_state["players"])):
        if other_seat == dying_seat:
            continue
        other_motion = _proposed_head(
            pre_state, other_seat, actions.get(other_seat) or {}, effects
        )
        if other_motion is None:
            continue
        d = _distance_between_segments(motion_p0, motion_p1, *other_motion)
        _consider(f"seat {other_seat} proposed head", d)
        if d <= _OBSTACLE_REACH:
            return

    pytest.fail(
        f"unexplained elimination: tick={tick_no}, policy={policy_name}, "
        f"seat={dying_seat}, motion=({motion_p0[0]:.4f},{motion_p0[1]:.4f})→"
        f"({motion_p1[0]:.4f},{motion_p1[1]:.4f}); nearest obstacle was "
        f"{best_obstacle[1] if best_obstacle else '<none>'} at distance "
        f"{best_obstacle[0]:.3f} (allowed: ≤ {_OBSTACLE_REACH:.3f}). The "
        f"engine killed this seat without anything close enough to be the "
        f"cause — likely a collision-detector false positive."
    )


# ─── the actual property test ───────────────────────────────────────────────


def test_prod_replay_m_17eb7f9d_tick450_does_not_kill_seat_0() -> None:
    """End-to-end regression against real production data.

    Loads the engine state at tick 449 from prod match
    m_17eb7f9d0a3d46e3 (a 450-tick human curve game) and steps the
    engine forward once with seat 0's recorded action (STRAIGHT). With
    the pre-fix `_segments_intersect`, the engine killed seat 0 by a
    false-positive collision against trail segment 445→446 (segments
    collinear with disjoint bounding boxes 23.5 units apart). With the
    AABB prefilter, seat 0 survives this step.

    Property: a real-life floating-point trap, reproduced exactly from
    journaled state — survives even when the scripted-policy property
    test above happens not to land on the buggy FP pattern.
    """
    import json
    from pathlib import Path

    fixture_path = (
        Path(__file__).parent / "fixtures" / "curve_m_17eb7f9d_tick449.json"
    )
    fixture = json.loads(fixture_path.read_text())
    state = fixture["state"]
    # The replay journals the trails as lists-of-lists; the engine treats
    # them as lists-of-tuples in some code paths. Normalize.
    state["trails"] = [
        [tuple(p) for p in trail] for trail in state["trails"]
    ]
    state["trail_delta"] = [
        [tuple(p) for p in d] for d in state["trail_delta"]
    ]
    assert state["tick"] == 449
    assert all(
        p["seat"] == fixture["next_action_seat"]
        and p["alive"]
        for p in state["players"]
        if p["seat"] == fixture["next_action_seat"]
    ), "fixture sanity: seat 0 must be alive at tick 449"

    curve = Curve()
    # All alive seats need an action; we don't know seats 1-3's exact
    # actions at tick 450 but they're all dead by tick 449, so we just
    # supply STRAIGHT defensively.
    actions = {p["seat"]: {"turn": "STRAIGHT"} for p in state["players"] if p["alive"]}
    actions[fixture["next_action_seat"]] = fixture["next_action"]
    result = curve.step(state, actions)

    new_seat_0 = next(p for p in result.state["players"] if p["seat"] == 0)
    assert new_seat_0["alive"], (
        "seat 0 was killed by a false-positive collision at tick 450 "
        "— this is the m_17eb7f9d0a3d46e3 bug. The AABB prefilter in "
        "`_segments_intersect` must have been reverted."
    )
    assert 0 not in result.eliminated_this_tick


@pytest.mark.parametrize("policy", list(_POLICIES.keys()))
@pytest.mark.parametrize("seed", [12345, 99, 17, 2026])
def test_no_unexplained_eliminations(seed: int, policy: str) -> None:
    """For every elimination across long matches under several scripted
    turn policies, the dying seat must have a real obstacle within
    reach of its proposed motion segment.

    This is the regression net for the
    `_segments_intersect`-style false-positive bug class: the prefix's
    collinear-disjoint trap, the next algorithmic mistake we make in
    collision detection, anything that lets the engine kill a player
    without a real cause."""
    curve = Curve()
    rng = random.Random(seed)
    policy_fn = _POLICIES[policy]
    state = curve.initial_state(seed=seed, num_players=4)

    for tick_no in range(curve.meta.max_ticks):
        # `actions` must be assembled BEFORE step() so we can replay the
        # exact same proposed motions when checking the invariant.
        actions = {
            seat: {"turn": policy_fn(rng, tick_no, seat)}
            for seat in range(4)
            if any(
                p["seat"] == seat and p["alive"]
                for p in state["players"]
            )
        }
        result = curve.step(state, actions)
        for seat in result.eliminated_this_tick:
            _assert_elimination_explainable(
                pre_state=state,
                dying_seat=seat,
                actions=actions,
                policy_name=policy,
                tick_no=tick_no + 1,
            )
        state = result.state
        if result.done:
            break
