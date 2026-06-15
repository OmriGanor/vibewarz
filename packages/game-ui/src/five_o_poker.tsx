"use client";

import { useMemo } from "react";
import { PlaybackControls, usePlayback } from "./controls";
import { ReplayFrame } from "./frame";
import { FiveOPokerBoard, type SeatInfo } from "./five_o_poker/board";
import type { FiveOPokerState } from "./five_o_poker/types";
import { seatLabel, type RawEvent, type RawGameEndEvt } from "./types";

type Frame = { state: FiveOPokerState };

export function buildFiveOPokerFrames(events: RawEvent[]): Frame[] {
  const frames: Frame[] = [];
  for (const evt of events) {
    if (evt.type === "game_start" || evt.type === "tick_result") {
      frames.push({ state: evt.state as FiveOPokerState });
    }
  }
  return frames;
}

const FIVE_O_POKER_TICKS_PER_SEC = 2;

export function FiveOPokerReplay({
  events,
}: {
  events: RawEvent[];
}) {
  const frames = useMemo(() => buildFiveOPokerFrames(events), [events]);
  const totalFrames = frames.length;
  const playback = usePlayback(totalFrames, FIVE_O_POKER_TICKS_PER_SEC);
  const current = frames[Math.min(playback.frame, Math.max(0, totalFrames - 1))];
  const finalPlacement =
    (events[events.length - 1] as RawGameEndEvt | undefined)?.placement ?? [];

  const seats = useMemo<number[]>(() => {
    const first = frames[0]?.state;
    if (!first) return [];
    return first.players.map((p) => p.seat).sort((a, b) => a - b);
  }, [frames]);

  const seatInfo = useMemo<SeatInfo[]>(
    () =>
      seats.map((s) => ({
        seat: s,
        handle: seatLabel(events, s),
        is_bot: false,
        bot_label: null,
      })),
    [seats, events],
  );

  if (totalFrames === 0 || !current) {
    return <div className="vw-replay vw-replay__empty">empty replay</div>;
  }

  const winnerSeat = finalPlacement[0];
  const atEnd = playback.frame >= totalFrames - 1;
  const brand =
    atEnd && winnerSeat !== undefined ? (
      <span className="vw-frame__result">🏆 {seatLabel(events, winnerSeat)}</span>
    ) : undefined;

  return (
    <div className="vw-replay">
      <ReplayFrame
        ratio="16:9"
        nativeRatio="16:9"
        brand={brand}
      >
        <FiveOPokerBoard
          state={current.state}
          seatInfo={seatInfo}
        />
      </ReplayFrame>
      <PlaybackControls
        totalFrames={totalFrames}
        currentTick={current.state.tick}
        maxTick={frames[totalFrames - 1].state.tick}
        playback={playback}
      />
    </div>
  );
}
