"""Vibelords — deterministic lane combat resolution.

One pure function, ``resolve_tick``, advances the battlefield by a single tick:

  1. From the *start-of-tick snapshot*, every unit picks a target — the nearest
     enemy unit within its attack range, else the enemy base if it has marched
     into reach. A unit with a target is "engaged" and holds position; a unit
     with none advances toward the enemy base.
  2. Engaged units whose attack cooldown is ready register damage (with the RPS
     multiplier vs units; flat vs bases). All damage is gathered against the
     snapshot, then applied at once — so combat is simultaneous and independent
     of iteration order.
  3. Dead units are removed; cooldowns tick; survivors that were not engaged
     move. Visual ``fx`` (hits, arrows, deaths) are emitted for the renderer.

No randomness, no I/O, no mutation of the caller's lists beyond the copies it is
handed. Determinism is guaranteed by ordering all tie-breaks on ``(x, id)``.
"""

from __future__ import annotations

from . import units as U


def _enemy_base_x(owner: int, lane_length: float) -> float:
    """The x-coordinate of the base ``owner`` is marching toward."""
    return lane_length if owner == 0 else 0.0


def resolve_tick(
    unit_list: list[dict],
    bases: list[dict],
    lane_length: float,
) -> tuple[list[dict], list[dict], list[dict], dict[int, float]]:
    """Advance combat one tick.

    Args are already-copied mutable structures. Returns
    ``(surviving_units, dead_units, fx, dmg_by_owner)`` where ``dead_units`` are
    the unit dicts that died this tick (for kill-reward attribution) and
    ``dmg_by_owner`` maps an owner seat to the damage its units dealt this tick
    (used for the timeout tie-break).
    """
    # Resolve static stats once per unit (id -> stat block).
    stats = {u["id"]: U.unit_stats(u["unit"], u["age"]) for u in unit_list}
    base_x = {b["seat"]: b["x"] for b in bases}

    dmg_to_unit: dict[str, float] = {}
    dmg_to_base: dict[int, float] = {}
    dmg_by_owner: dict[int, float] = {}
    attacked: set[str] = set()
    movers: list[dict] = []
    fx: list[dict] = []

    ordered = sorted(unit_list, key=lambda u: (u["x"], u["id"]))
    for u in ordered:
        st = stats[u["id"]]
        rng = st["range"]
        enemies = [e for e in unit_list if e["owner"] != u["owner"]]
        in_range = [e for e in enemies if abs(e["x"] - u["x"]) <= rng]

        target_unit: dict | None = None
        if in_range:
            target_unit = min(in_range, key=lambda e: (abs(e["x"] - u["x"]), e["id"]))

        enemy_seat = 1 - u["owner"]
        ebx = base_x.get(enemy_seat, _enemy_base_x(u["owner"], lane_length))
        base_in_range = (
            bases[enemy_seat]["hp"] > 0 and abs(ebx - u["x"]) <= rng
        )

        if target_unit is None and not base_in_range:
            movers.append(u)
            continue

        # Engaged — hold position. Fire if the cooldown is ready.
        if u["atk_cd"] > 0:
            continue

        attacked.add(u["id"])
        if target_unit is not None:
            mult = U.damage_multiplier(u["unit"], target_unit["unit"])
            dealt = st["atk"] * mult
            dmg_to_unit[target_unit["id"]] = (
                dmg_to_unit.get(target_unit["id"], 0.0) + dealt
            )
            fx.append(
                {
                    "kind": "arrow" if u["unit"] == "archer" else "hit",
                    "owner": u["owner"],
                    "age": u["age"],
                    "x0": u["x"],
                    "x1": target_unit["x"],
                    "crit": mult > 1.0,
                }
            )
        else:
            dealt = st["atk"]
            dmg_to_base[enemy_seat] = dmg_to_base.get(enemy_seat, 0.0) + dealt
            fx.append(
                {
                    "kind": "arrow" if u["unit"] == "archer" else "hit",
                    "owner": u["owner"],
                    "age": u["age"],
                    "x0": u["x"],
                    "x1": ebx,
                    "crit": False,
                }
            )
        dmg_by_owner[u["owner"]] = dmg_by_owner.get(u["owner"], 0.0) + dealt

    # Apply damage to bases.
    for seat, dmg in dmg_to_base.items():
        bases[seat]["hp"] = max(0, bases[seat]["hp"] - dmg)

    # Apply damage to units, then split living from dead.
    survivors: list[dict] = []
    dead: list[dict] = []
    for u in unit_list:
        hp = u["hp"] - dmg_to_unit.get(u["id"], 0.0)
        if hp <= 0:
            dead.append(u)
            fx.append(
                {"kind": "death", "owner": u["owner"], "unit": u["unit"], "x": u["x"]}
            )
            continue
        u["hp"] = hp
        survivors.append(u)

    # Cooldowns: attackers reset, everyone else ticks down.
    for u in survivors:
        if u["id"] in attacked:
            u["atk_cd"] = stats[u["id"]]["atk_cd"]
        elif u["atk_cd"] > 0:
            u["atk_cd"] -= 1

    # Movement for the unengaged survivors (dead ones already filtered out).
    moving = {u["id"] for u in movers}
    for u in survivors:
        if u["id"] not in moving:
            continue
        st = stats[u["id"]]
        direction = 1.0 if u["owner"] == 0 else -1.0
        ebx = _enemy_base_x(u["owner"], lane_length)
        nx = u["x"] + direction * st["speed"]
        # Don't march past the enemy base.
        u["x"] = min(nx, ebx) if direction > 0 else max(nx, ebx)

    return survivors, dead, fx, dmg_by_owner
