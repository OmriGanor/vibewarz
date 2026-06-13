"use client";

// End-of-hand win / payout animation. Driven purely by engine state — it
// renders whenever `phase` is "hand_complete" (a single hand resolved) or
// "done" (the tournament ended), reading `pot_distribution` for the split and
// `showdown_hands` for the winning-hand name. Because it's a pure function of
// state, the SAME overlay shows in replays and in live play; only the timing
// differs (replay playback dwells on the frame for REPLAY_PAYOUT_MS; live
// latches via PokerBoard's `resultHoldMs` for LIVE_PAYOUT_MS). All sub-timings
// scale to the `payoutMs` window so the same choreography fits a 1s replay
// cheer or a 3s gameplay cheer. See board.tsx for how it's mounted and re-keyed
// per hand so the animation re-fires each round.

import type { CSSProperties } from "react";

import { ChipPile } from "./chip";
import type { PokerState } from "./types";
import type { SeatInfo } from "./board";

// Table center, matching the community-cards / pot anchor in board.tsx. The
// won chips fly out from here toward each winner.
const POT_X = 50;
const POT_Y = 44;
// How far from a seat toward the pot the landed chips + amount badge sit (so
// they rest on the felt in front of the winner, clear of the seat plate).
const LAND_T = 0.28;

// Group thousands deterministically (locale-pinned) so chip amounts read like
// "1,980" identically across machines/replays.
const fmtChips = (n: number): string => n.toLocaleString("en-US");

// The engine emits one `pot_distribution` entry per pot layer / split share, so
// a single seat can appear several times (main pot + side pots). Sum per seat
// for display.
export function winningsBySeat(
  dist: { seat: number; amount: number }[],
): Map<number, number> {
  const m = new Map<number, number>();
  for (const d of dist) m.set(d.seat, (m.get(d.seat) ?? 0) + d.amount);
  return m;
}

export function PayoutOverlay({
  state,
  positions,
  anchor,
  n,
  seatInfo,
  counterRotate = "",
  payoutMs,
}: {
  state: PokerState;
  // Seat percentage positions for an n-seat table (board.tsx TABLE_POSITIONS),
  // indexed by clockwise offset from `anchor`.
  positions: { x: number; y: number }[];
  // Seat rendered bottom-center (offset 0) — the POV/you anchor.
  anchor: number;
  n: number;
  seatInfo?: SeatInfo[];
  // Appended to readable elements' transforms to keep them upright while the
  // table is spun in portrait (e.g. " rotate(-90deg)").
  counterRotate?: string;
  // Total cheer duration; every sub-animation is a fraction of this so the
  // choreography fits a short (replay) or long (gameplay) window.
  payoutMs: number;
}) {
  const dist = state.pot_distribution;
  if (!dist || dist.length === 0) return null;

  const winnings = winningsBySeat(dist);
  // Biggest winner first — drives the headline and badge stagger.
  const winners = [...winnings.keys()].sort(
    (a, b) => (winnings.get(b) ?? 0) - (winnings.get(a) ?? 0),
  );
  if (winners.length === 0) return null;

  const isDone = state.phase === "done";
  const handleBySeat = new Map((seatInfo ?? []).map((s) => [s.seat, s]));
  const colorBySeat = new Map(state.players.map((p) => [p.seat, p.color]));
  const label = (seat: number): string =>
    handleBySeat.get(seat)?.handle ?? `seat ${seat}`;

  // At "done" the headline names the tournament winner (placement[0]); during a
  // hand it names the pot winner(s).
  const headlineSeat = isDone ? state.placement[0] ?? winners[0] : winners[0];
  const handName = state.showdown_hands?.[String(headlineSeat)] ?? null;
  const isSplit = winners.length > 1;
  const wentToShowdown = state.showdown_hands !== null;

  let title: string;
  if (isDone) {
    title = `🏆 ${label(headlineSeat)} wins the tournament`;
  } else if (isSplit) {
    title = "Split pot";
  } else {
    title = `${label(headlineSeat)} wins ${fmtChips(winnings.get(headlineSeat) ?? 0)}`;
  }
  // Subtitle: the made hand at a showdown, or "uncontested" for a fold-around.
  const subtitle = handName
    ? handName
    : !wentToShowdown && !isDone
      ? "uncontested"
      : null;

  return (
    <div
      className={"vw-poker__payout" + (isDone ? " vw-poker__payout--final" : "")}
      style={{ "--vw-payout-dur": `${payoutMs}ms` } as CSSProperties}
      role="status"
      aria-live="polite"
    >
      <div className="vw-poker__payout-scrim" aria-hidden />

      <Confetti originX={POT_X} originY={46} count={isDone ? 48 : 22} big={isDone} />

      {winners.map((seat, i) => {
        const offset = (seat - anchor + n) % n;
        const pos = positions[offset] ?? positions[0];
        const landX = pos.x + (POT_X - pos.x) * LAND_T;
        const landY = pos.y + (POT_Y - pos.y) * LAND_T;
        return (
          <SeatPayout
            key={seat}
            landX={landX}
            landY={landY}
            amount={winnings.get(seat) ?? 0}
            counterRotate={counterRotate}
            delayMs={i * payoutMs * 0.06}
            payoutMs={payoutMs}
          />
        );
      })}

      <div
        className="vw-poker__payout-banner"
        style={{ transform: `translate(-50%, -50%)${counterRotate}` }}
      >
        <div className="vw-poker__payout-title">{title}</div>
        {subtitle && <div className="vw-poker__payout-sub">{subtitle}</div>}
      </div>
    </div>
  );
}

// One winner's chips sliding from the pot to in front of their seat, plus the
// "+amount" badge that pops once the chips land. The chip count is drawn
// proportional to the actual amount (ChipPile breaks it into denominations).
function SeatPayout({
  landX,
  landY,
  amount,
  counterRotate,
  delayMs,
  payoutMs,
}: {
  landX: number;
  landY: number;
  amount: number;
  counterRotate: string;
  delayMs: number;
  payoutMs: number;
}) {
  // CSS animates `left`/`top` from the pot to the landing spot via these vars
  // (resolved per-element inside the @keyframes). Chip discs need no
  // counter-rotation in portrait; only the readable badge does.
  const flyVars: CSSProperties = {
    "--vw-from-x": `${POT_X}%`,
    "--vw-from-y": `${POT_Y}%`,
    "--vw-to-x": `${landX}%`,
    "--vw-to-y": `${landY}%`,
    transform: "translate(-50%, -50%)",
    animationDelay: `${delayMs}ms`,
  } as CSSProperties;

  return (
    <>
      <div className="vw-poker__payout-pile" style={flyVars} aria-hidden>
        <ChipPile amount={amount} unit={13} />
      </div>
      <div
        className="vw-poker__payout-badge"
        style={{
          left: `${landX}%`,
          top: `${landY}%`,
          transform: `translate(-50%, -50%)${counterRotate}`,
          animationDelay: `${delayMs + payoutMs * 0.32}ms`,
        }}
      >
        +{fmtChips(amount)}
      </div>
    </>
  );
}

// A celebratory burst from (originX, originY)%. Particle vectors are derived
// from the index (no RNG) so it's deterministic across replays. `big` widens
// the spread and biases it downward for the tournament-win finale.
function Confetti({
  originX,
  originY,
  count,
  big,
}: {
  originX: number;
  originY: number;
  count: number;
  big: boolean;
}) {
  const colors = [
    "#f43f5e",
    "#a3e635",
    "#3b82f6",
    "#f59e0b",
    "#a855f7",
    "#10b981",
    "#fde047",
  ];
  const reach = big ? 200 : 130;
  const gravity = big ? 150 : 90;
  return (
    <div className="vw-poker__confetti" aria-hidden>
      {Array.from({ length: count }).map((_, i) => {
        const angle = (i / count) * Math.PI * 2;
        const dist = reach * (0.5 + ((i % 5) / 5) * 0.5);
        const dx = Math.cos(angle) * dist;
        const dy = Math.sin(angle) * dist + gravity;
        const rot = (i % 2 ? 1 : -1) * (180 + (i % 4) * 150);
        return (
          <span
            key={i}
            className="vw-poker__confetti-bit"
            style={
              {
                left: `${originX}%`,
                top: `${originY}%`,
                background: colors[i % colors.length],
                "--vw-c-dx": `${dx.toFixed(1)}px`,
                "--vw-c-dy": `${dy.toFixed(1)}px`,
                "--vw-c-r": `${rot}deg`,
                animationDelay: `${(i % 6) * (big ? 45 : 30)}ms`,
              } as CSSProperties
            }
          />
        );
      })}
    </div>
  );
}
