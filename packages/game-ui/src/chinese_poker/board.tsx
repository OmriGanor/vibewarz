"use client";

import { type CSSProperties } from "react";
import { Card } from "../poker/card";
import type { ChinesePokerPlayer, ChinesePokerState, ChinesePokerAction } from "./types";

const MONO = "ui-monospace, 'JetBrains Mono', Menlo, Consolas, monospace";

export type SeatInfo = {
  seat: number;
  handle: string;
  is_bot: boolean;
  bot_label: string | null;
};

const headerCell: CSSProperties = {
  fontFamily: MONO,
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: "0.18em",
  color: "var(--vw-color-text-muted)",
};

function actionLabel(a: ChinesePokerPlayer["last_action"]): string | null {
  if (!a) return null;
  if (a.type === "place") return `place col ${a.column + 1}`;
  return null;
}

export function ChinesePokerBoard({
  state,
  seatInfo,
  onAction,
  humanSeat,
}: {
  state: ChinesePokerState | null;
  seatInfo?: SeatInfo[];
  onAction?: (action: ChinesePokerAction) => void;
  humanSeat?: number;
}) {
  const handleBySeat = new Map(seatInfo?.map((s) => [s.seat, s]) ?? []);
  if (!state) {
    return (
      <div
        style={{
          borderRadius: 16,
          padding: 48,
          textAlign: "center",
          color: "var(--vw-color-text-muted)",
          background: "linear-gradient(180deg, #1a1a1f 0%, #0a0a0b 100%)",
        }}
      >
        waiting for game to start…
      </div>
    );
  }

  const handleFor = (seat: number) =>
    handleBySeat.get(seat)?.handle ?? `Seat ${seat}`;

  let resultText: string | null = null;
  if (state.phase === "done") {
    if (state.winner === -1 || state.winner == null) {
      resultText = "Draw";
    } else if (state.winner === humanSeat) {
      resultText = "You Won!";
    } else {
      resultText = `${handleFor(state.winner)} Won!`;
    }
  }

  return (
    <div
      className="vw-chinese-poker__board"
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: "radial-gradient(ellipse at center, #111827 0%, #030712 100%)",
        borderRadius: 16,
        padding: "16px 24px",
        overflow: "hidden",
        boxSizing: "border-box",
      }}
    >
      {/* Header Info */}
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <div style={{ display: "flex", gap: "1rem", alignItems: "baseline" }}>
          <span style={{ ...headerCell, color: "var(--vw-color-accent)" }}>
            Chinese Poker
          </span>
          <span style={headerCell}>{state.phase}</span>
        </div>
      </div>

      {/* Game Over Banner */}
      {resultText && (
        <div style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          background: "rgba(0,0,0,0.85)",
          border: "2px solid var(--vw-color-accent)",
          padding: "24px 48px",
          borderRadius: 16,
          zIndex: 50,
          textAlign: "center",
          boxShadow: "0 0 40px rgba(163, 230, 53, 0.2)",
          backdropFilter: "blur(4px)",
        }}>
          <h2 style={{ fontFamily: MONO, color: "var(--vw-color-accent)", margin: 0, fontSize: 24, textTransform: "uppercase", letterSpacing: "0.1em" }}>
            {resultText}
          </h2>
        </div>
      )}

      {/* Board Layout */}
      <div style={{ display: "flex", flex: 1, gap: 24, justifyContent: "space-around", alignItems: "center" }}>
        {state.players.map((player) => {
          const info = handleBySeat.get(player.seat);
          const isActor = state.action_on === player.seat;
          const showDrawn = isActor && state.phase === "placing" && state.current_drawn_card;
          const isInteractivePlacing =
            isActor && player.seat === humanSeat && state.phase === "placing" && !!onAction;

          return (
            <div
              key={player.seat}
              style={{
                background: "rgba(255, 255, 255, 0.02)",
                border: isActor
                  ? "2px solid var(--vw-color-accent)"
                  : "1px solid rgba(255, 255, 255, 0.05)",
                borderRadius: 12,
                padding: 16,
                width: "45%",
                display: "flex",
                flexDirection: "column",
                gap: 12,
                boxShadow: isActor ? "0 0 16px rgba(163, 230, 53, 0.2)" : "none",
                position: "relative",
              }}
            >
              {/* Player Header */}
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: MONO }}>
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: player.seat === 0 ? "#a3e635" : "#f43f5e",
                  }}
                />
                <span style={{ color: "#fff", fontWeight: 600 }}>
                  {info?.handle ?? `seat ${player.seat}`}
                </span>
              </div>

              {/* Hands */}
              <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 6 }}>
                {player.columns.map((col, idx) => {
                  const showdownLabel = state.showdown_hands?.[String(player.seat)]?.[idx];
                  const isWinner = state.winning_columns?.[String(player.seat)]?.includes(idx);
                  return (
                    <div
                      key={idx}
                      onClick={() => {
                        if (isInteractivePlacing && onAction) {
                          onAction({ type: "place", column: idx });
                        }
                      }}
                      style={{
                        display: "flex",
                        flexDirection: "row",
                        alignItems: "center",
                        gap: 4,
                        flex: 1,
                        background: isWinner ? "rgba(163, 230, 53, 0.15)" : (isInteractivePlacing ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.2)"),
                        border: isWinner ? "1px solid var(--vw-color-accent)" : "1px solid transparent",
                        boxShadow: isWinner ? "0 0 12px rgba(163, 230, 53, 0.3)" : "none",
                        borderRadius: 8,
                        padding: "3px 7px",
                        cursor: isInteractivePlacing ? "pointer" : "default",
                      }}
                    >
                      <div style={{ fontSize: 10, fontFamily: MONO, color: isWinner ? "var(--vw-color-accent)" : "var(--vw-color-text-muted)", width: 20 }}>
                        H{idx + 1}
                      </div>
                      {/* Cards in hand */}
                      {Array.from({ length: 5 }).map((_, cIdx) => {
                        const card = col[cIdx];
                        if (!card) {
                          return (
                            <div
                              key={cIdx}
                              style={{
                                width: 32,
                                height: 46,
                                border: "1px dashed rgba(255,255,255,0.06)",
                                borderRadius: 4,
                              }}
                            />
                          );
                        }
                        return (
                          <Card
                            key={cIdx}
                            card={card === "??" ? null : card}
                            size="sm"
                          />
                        );
                      })}
                      {showdownLabel && (
                        <div
                          style={{
                            fontSize: 9,
                            fontFamily: MONO,
                            color: "#fff",
                            marginLeft: "auto",
                            lineHeight: 1.1,
                          }}
                        >
                          {showdownLabel}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Current action text */}
              {player.last_action && (
                <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vw-color-accent)", textAlign: "center" }}>
                  {actionLabel(player.last_action)}
                </div>
              )}

              {/* Drawn card if active placer */}
              {showDrawn && (
                <div
                  style={{
                    position: "absolute",
                    bottom: -20,
                    left: "50%",
                    transform: "translateX(-50%)",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 2,
                    zIndex: 10,
                  }}
                >
                  <span style={{ fontSize: 9, fontFamily: MONO, color: "var(--vw-color-accent)", textTransform: "uppercase" }}>
                    Drawn
                  </span>
                  <Card card={state.current_drawn_card} size="md" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
