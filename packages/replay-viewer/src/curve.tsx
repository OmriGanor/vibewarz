"use client";

import { useEffect, useMemo, useRef } from "react";

import { PlaybackControls, usePlayback } from "./controls";
import type { RawEvent, RawGameEndEvt } from "./types";

type PowerupKind = "speed" | "slow" | "god";
type Powerup = { id: string; kind: PowerupKind; x: number; y: number };

type CurveState = {
  tick: number;
  arena: { w: number; h: number };
  speed: number;
  turn_rate_deg: number;
  players: {
    seat: number;
    x: number;
    y: number;
    heading_deg: number;
    alive: boolean;
    color: string;
    effects?: Partial<Record<PowerupKind, number>>;
  }[];
  trails?: [number, number][][];
  trail_delta?: [number, number][][];
  placement: number[];
  powerups?: Powerup[];
};

const POWERUP_COLORS: Record<PowerupKind, string> = {
  speed: "#22c55e",
  slow: "#ef4444",
  god: "#a855f7",
};

function powerupFill(kind: PowerupKind, tick: number): string {
  if (kind === "god") return `hsl(${(tick * 8) % 360}, 90%, 60%)`;
  return POWERUP_COLORS[kind];
}

// Engine default — keep in sync with games/.../curve/game.py POWERUP_DURATION.
const GOD_MAX_TICKS = 50;

type CurvePlayerLite = {
  seat: number;
  alive: boolean;
  color: string;
  effects?: Partial<Record<PowerupKind, number>>;
};

function headColor(
  player: CurvePlayerLite,
  all: readonly CurvePlayerLite[],
  tick: number,
): string {
  const effects = player.effects ?? {};

  if (effects.god && effects.god > 0) {
    const period = Math.max(2, Math.floor((effects.god / GOD_MAX_TICKS) * 10));
    return Math.floor(tick / period) % 2 === 0
      ? powerupFill("god", tick)
      : "#ffffff";
  }

  if (effects.speed && effects.speed > 0) return POWERUP_COLORS.speed;

  if (!(effects.slow && effects.slow > 0)) {
    const slowedByOther = all.some(
      (o) =>
        o.seat !== player.seat &&
        o.alive &&
        (o.effects?.slow ?? 0) > 0,
    );
    if (slowedByOther) return POWERUP_COLORS.slow;
  }

  return player.color;
}

type Frame = { state: CurveState };

export function buildCurveFrames(events: RawEvent[]): Frame[] {
  const frames: Frame[] = [];
  let trails: [number, number][][] | null = null;

  for (const evt of events) {
    if (evt.type === "game_start") {
      const s = evt.state as CurveState;
      trails = (s.trails ?? s.players.map((p) => [[p.x, p.y]])).map((t) =>
        t.map((pt) => [pt[0], pt[1]] as [number, number]),
      );
      frames.push({
        state: { ...s, trails: trails.map((t) => t.slice()) },
      });
    } else if (evt.type === "tick_result") {
      if (!trails) continue;
      const s = evt.state as CurveState;
      const delta = s.trail_delta ?? [];
      for (let seat = 0; seat < delta.length; seat++) {
        for (const pt of delta[seat]) {
          trails[seat].push([pt[0], pt[1]] as [number, number]);
        }
      }
      frames.push({
        state: { ...s, trails: trails.map((t) => t.slice()) },
      });
    }
    // game_end: final state already shown via the last tick_result.
  }
  return frames;
}

// Curve: tick_interval_ms=50 → 20 Hz live cadence.
const CURVE_TICKS_PER_SEC = 20;

export function CurveReplay({ events }: { events: RawEvent[] }) {
  const frames = useMemo(() => buildCurveFrames(events), [events]);
  const totalFrames = frames.length;
  const playback = usePlayback(totalFrames, CURVE_TICKS_PER_SEC);
  const current = frames[Math.min(playback.frame, Math.max(0, totalFrames - 1))];
  const finalPlacement =
    (events[events.length - 1] as RawGameEndEvt | undefined)?.placement ?? [];

  if (totalFrames === 0 || !current) {
    return <div className="vw-replay vw-replay__empty">empty replay</div>;
  }

  return (
    <div className="vw-replay">
      <div className="vw-replay__layout">
        <div>
          <CurveBoard state={current.state} />
          <PlaybackControls
            totalFrames={totalFrames}
            currentTick={current.state.tick}
            maxTick={frames[totalFrames - 1].state.tick}
            playback={playback}
          />
        </div>
        <aside className="vw-replay__sidebar">
          {current.state.players.map((p) => {
            const finalPos = finalPlacement.indexOf(p.seat);
            return (
              <div
                key={p.seat}
                className={
                  "vw-replay__player" +
                  (p.alive ? "" : " vw-replay__player--dead")
                }
              >
                <div className="vw-replay__player-row">
                  <div
                    className="vw-replay__player-chip"
                    style={{ backgroundColor: p.color }}
                  />
                  <p className="vw-replay__player-name">seat {p.seat}</p>
                  <span
                    className={
                      "vw-replay__player-status " +
                      (p.alive
                        ? "vw-replay__player-status--alive"
                        : "vw-replay__player-status--dead")
                    }
                  >
                    {p.alive ? "alive" : "dead"}
                  </span>
                </div>
                {finalPos >= 0 && (
                  <p className="vw-replay__player-finish">
                    final: #{finalPos + 1}
                  </p>
                )}
              </div>
            );
          })}
        </aside>
      </div>
    </div>
  );
}

function CurveBoard({ state }: { state: CurveState }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const size = 720;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    ctx.fillStyle = "#0a0a0b";
    ctx.fillRect(0, 0, size, size);

    ctx.strokeStyle = "#181820";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
      const p = (i / 10) * size;
      ctx.beginPath();
      ctx.moveTo(p, 0);
      ctx.lineTo(p, size);
      ctx.moveTo(0, p);
      ctx.lineTo(size, p);
      ctx.stroke();
    }

    ctx.strokeStyle = "#2a2a30";
    ctx.lineWidth = 1;
    ctx.strokeRect(0.5, 0.5, size - 1, size - 1);

    if (!state.trails) return;
    const scale = size / state.arena.w;

    for (let seat = 0; seat < state.trails.length; seat++) {
      const trail = state.trails[seat];
      if (trail.length < 2) continue;
      const color = state.players[seat]?.color ?? "#fff";
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.beginPath();
      ctx.moveTo(trail[0][0] * scale, trail[0][1] * scale);
      for (let i = 1; i < trail.length; i++) {
        ctx.lineTo(trail[i][0] * scale, trail[i][1] * scale);
      }
      ctx.stroke();
    }

    for (const pu of state.powerups ?? []) {
      const x = pu.x * scale;
      const y = pu.y * scale;
      const fill = powerupFill(pu.kind, state.tick);
      ctx.beginPath();
      ctx.arc(x, y, 12, 0, Math.PI * 2);
      ctx.fillStyle = fill + "33";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.fillStyle = fill;
      ctx.fill();
    }

    for (const p of state.players) {
      if (!p.alive) continue;
      const x = p.x * scale;
      const y = p.y * scale;
      const head = headColor(p, state.players, state.tick);
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI * 2);
      ctx.fillStyle = head;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(x, y, 10, 0, Math.PI * 2);
      ctx.fillStyle = head + "33";
      ctx.fill();
    }
  }, [state]);

  return (
    <div className="vw-replay__board">
      <canvas ref={canvasRef} />
    </div>
  );
}
