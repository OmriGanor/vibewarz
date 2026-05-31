"""Vibelords — unit roster, the rock-paper-scissors counter map, and per-age
stat scaling.

Three unit classes form a counter cycle:

    pike  >  cavalry  >  archer  >  pike

The counter relationship is enforced two ways so it is not merely an abstract
multiplier:

  * an attacker deals ``ADVANTAGE_MULT`` times damage against the class it
    counters, and
  * the *mechanics* reinforce it — pikes are tanky anti-charge walls, cavalry
    are fast enough to run archers down, and archers out-range pikes and shoot
    them to pieces before they ever close.

Stats scale up each age (``hp``/``atk``/cost grow) while *positioning* stats
(``range``/``speed``/``atk_cd``/``build_ticks``) stay constant, so the duel
timing of any matchup is identical across ages — only the raw power escalates.
A higher-age unit beats its lower-age counterpart of the same class.

Everything here is pure data + pure helpers (no state, no I/O).
"""

from __future__ import annotations

from typing import Final

# Counter cycle: key beats value (deals ADVANTAGE_MULT damage to it).
UNIT_TYPES: Final = ("pike", "cavalry", "archer")
COUNTERS: Final = {"pike": "cavalry", "cavalry": "archer", "archer": "pike"}
ADVANTAGE_MULT: Final = 2.2

NUM_AGES: Final = 4
AGE_NAMES: Final = ("Stone", "Castle", "Industrial", "Future")

# XP required to advance INTO age i (index == target age). Index 0 unused
# (everyone starts in the Stone age). Rising cost makes teching a real tempo
# sacrifice rather than an automatic play.
AGE_UP_XP_COST: Final = (0, 120, 320, 700)

# Per-age multipliers applied to the age-0 base stats below.
_POWER_SCALE: Final = 1.55  # hp & atk
_COST_SCALE: Final = 1.6    # gold cost & kill reward

# Age-0 base stat blocks. Positions are in lane units (lane is 1000 long).
# ``range``   — attack reach (archers out-range melee by ~5x).
# ``speed``   — lane units travelled per tick when not engaged.
# ``atk_cd``  — ticks between attacks.
# ``build_ticks`` — hidden build time before the unit deploys from the base.
_BASE_STATS: Final = {
    "pike": {
        "hp": 140, "atk": 18, "range": 16, "speed": 7, "atk_cd": 6,
        "gold_cost": 40, "build_ticks": 8, "kill_gold": 22, "kill_xp": 14,
    },
    "cavalry": {
        "hp": 100, "atk": 20, "range": 16, "speed": 15, "atk_cd": 6,
        "gold_cost": 55, "build_ticks": 9, "kill_gold": 30, "kill_xp": 16,
    },
    "archer": {
        "hp": 70, "atk": 22, "range": 85, "speed": 9, "atk_cd": 6,
        "gold_cost": 50, "build_ticks": 10, "kill_gold": 28, "kill_xp": 16,
    },
}


def counters(attacker_type: str, defender_type: str) -> bool:
    """True if ``attacker_type`` hard-counters ``defender_type``."""
    return COUNTERS.get(attacker_type) == defender_type


def damage_multiplier(attacker_type: str, defender_type: str) -> float:
    """RPS damage multiplier an attacker deals to a defender."""
    return ADVANTAGE_MULT if counters(attacker_type, defender_type) else 1.0


def age_up_cost(current_age: int) -> int | None:
    """XP needed to advance from ``current_age`` to the next, or None if maxed."""
    nxt = current_age + 1
    if nxt >= NUM_AGES:
        return None
    return AGE_UP_XP_COST[nxt]


def unit_stats(unit_type: str, age: int) -> dict:
    """Fully-resolved stat block for ``unit_type`` at ``age`` (age-scaled)."""
    base = _BASE_STATS[unit_type]
    power = _POWER_SCALE**age
    cost = _COST_SCALE**age
    return {
        "hp": round(base["hp"] * power),
        "atk": round(base["atk"] * power),
        "range": base["range"],
        "speed": base["speed"],
        "atk_cd": base["atk_cd"],
        "gold_cost": round(base["gold_cost"] * cost),
        "build_ticks": base["build_ticks"],
        "kill_gold": round(base["kill_gold"] * cost),
        "kill_xp": round(base["kill_xp"] * power),
    }
