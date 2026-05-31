// Types mirroring the Vibelords engine state in
// games/src/vibewarz_games/vibelords/game.py.

export type VibelordsUnitType = "pike" | "cavalry" | "archer";

export type VibelordsUnit = {
  id: string;
  owner: number;
  unit: VibelordsUnitType;
  age: number;
  x: number;
  hp: number;
  max_hp: number;
  atk_cd: number;
};

export type VibelordsQueueItem = { unit: VibelordsUnitType; age: number; ready_tick: number };

export type VibelordsPlayer = {
  seat: number;
  color: string;
  gold: number;
  xp: number;
  age: number;
  special_cd: number;
  dmg_dealt: number;
  // Hidden from the opponent's view; present (own) or [] (redacted) on the wire.
  queue: VibelordsQueueItem[];
};

export type VibelordsBase = {
  seat: number;
  x: number;
  hp: number;
  max_hp: number;
};

// Transient per-tick visual events emitted by the engine for the renderer.
export type VibelordsFx =
  | { kind: "hit"; owner: number; age?: number; x0: number; x1: number; crit: boolean }
  | { kind: "arrow"; owner: number; age?: number; x0: number; x1: number; crit: boolean }
  | { kind: "death"; owner: number; unit: VibelordsUnitType; x: number }
  | { kind: "airstrike"; owner: number; age?: number; x0: number; x1: number };

export type VibelordsState = {
  tick: number;
  max_ticks: number;
  lane: { length: number };
  bases: VibelordsBase[];
  players: VibelordsPlayer[];
  units: VibelordsUnit[];
  fx: VibelordsFx[];
  placement: number[];
};

export type VibelordsAction =
  | { type: "build"; unit: VibelordsUnitType }
  | { type: "advance_age" }
  | { type: "special" }
  | { type: "noop" };

// ── constants mirrored from game.py / units.py (visual scaling only) ──────────

// Vibelords run at tick_interval_ms=100 → 10 Hz live cadence.
export const VIBELORDS_TICKS_PER_SEC = 10;

// Special airstrike recharge, for the cooldown ring fill.
export const SPECIAL_CD_TICKS = 250;

export const AGE_NAMES = ["Stone", "Castle", "Industrial", "Future"] as const;
export const NUM_AGES = AGE_NAMES.length;

// XP required to advance INTO age i (index == target age).
export const AGE_UP_XP_COST = [0, 120, 320, 700] as const;

export function ageUpCost(age: number): number | null {
  const next = age + 1;
  return next >= NUM_AGES ? null : AGE_UP_XP_COST[next];
}

// Per-age display names for each role. The engine type (pike/cavalry/archer) is
// the stable identity used by bots and combat; these are flavour only, indexed
// [age]. Advancing an age re-skins the same three RPS roles into a new army.
export const UNIT_NAMES: Record<VibelordsUnitType, [string, string, string, string]> = {
  pike: ["Clubman", "Pikeman", "Trench Guard", "Juggernaut"],
  cavalry: ["Wolf Rider", "Knight", "Dragoon", "Hover Striker"],
  archer: ["Slinger", "Longbowman", "Rifleman", "Railgunner"],
};

export function unitDisplayName(type: VibelordsUnitType, age: number): string {
  return UNIT_NAMES[type]?.[Math.max(0, Math.min(NUM_AGES - 1, age))] ?? type;
}
