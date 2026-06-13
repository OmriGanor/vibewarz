"use client";

import { useState, type CSSProperties } from "react";
import { Card } from "../poker/card";
import { DealerButton } from "../poker/chip";
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
  if (a.type === "fold") return "fold";
  if (a.type === "check") return "check";
  if (a.type === "call") return "call";
  if (a.type === "raise") return `raise to ${(a as { to: number }).to}`;
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
  const [raiseAmount, setRaiseAmount] = useState<string>("");
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
        waiting for hand to start…
      </div>
    );
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
            hand #{state.hand_number}
          </span>
          <span style={headerCell}>{state.phase}</span>
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "baseline" }}>
          <span style={headerCell}>pot: {state.pot}</span>
        </div>
      </div>

      {/* Game Over Banner */}
      {state.phase === "done" && state.placement && state.placement.length > 0 && (
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
            {state.placement[0] === humanSeat ? "You Won!" : `${handleBySeat.get(state.placement[0])?.handle ?? `Seat ${state.placement[0]}`} Won!`}
          </h2>
        </div>
      )}

      {/* Hand Complete Banner */}
      {state.phase === "hand_complete" && (
        <div style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          background: "rgba(0,0,0,0.85)",
          border: "1px solid rgba(255,255,255,0.1)",
          padding: "24px 48px",
          borderRadius: 16,
          zIndex: 40,
          textAlign: "center",
          backdropFilter: "blur(4px)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
        }}>
          <h2 style={{ fontFamily: MONO, color: "#fff", margin: 0, fontSize: 18, textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Hand Complete
          </h2>
          {state.pot_distribution?.length === 1 ? (
            <h3 style={{ fontFamily: MONO, color: "var(--vw-color-accent)", margin: 0, fontSize: 20 }}>
              {state.pot_distribution[0].seat === humanSeat ? "You Won the Hand!" : `${handleBySeat.get(state.pot_distribution[0].seat)?.handle ?? `Seat ${state.pot_distribution[0].seat}`} Won the Hand!`}
            </h3>
          ) : state.pot_distribution?.length === 2 ? (
            <h3 style={{ fontFamily: MONO, color: "var(--vw-color-text-muted)", margin: 0, fontSize: 20 }}>
              Split Pot (Tie)
            </h3>
          ) : null}
          {onAction && state.action_on === humanSeat && (
            <button
              style={{
                background: "var(--vw-color-accent)",
                color: "#000",
                border: "none",
                padding: "8px 16px",
                borderRadius: 4,
                cursor: "pointer",
                fontFamily: MONO,
                fontWeight: "bold",
                fontSize: 14,
              }}
              onClick={() => onAction({ type: "ready" })}
            >
              Next Hand
            </button>
          )}
        </div>
      )}

      {/* Board Layout */}
      <div style={{ display: "flex", flex: 1, gap: 24, justifyContent: "space-around", alignItems: "center" }}>
        {state.players.map((player) => {
          const info = handleBySeat.get(player.seat);
          const isActor = state.action_on === player.seat;
          const showDrawn = isActor && state.phase === "placing" && state.current_drawn_card;
          
          const isHumanTurn = isActor && player.seat === humanSeat && onAction;
          const isInteractivePlacing = isHumanTurn && state.phase === "placing";
          const isInteractiveBetting = isHumanTurn && state.phase === "betting";

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
              {/* Dealer Button */}
              {state.button === player.seat && (
                <div style={{ position: "absolute", top: 8, right: 8 }}>
                  <DealerButton />
                </div>
              )}

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
                {player.all_in && (
                  <span style={{ color: "var(--vw-color-danger)", fontSize: 11, fontWeight: 700 }}>
                    ALL-IN
                  </span>
                )}
                {player.folded && (
                  <span style={{ color: "var(--vw-color-text-muted)", fontSize: 11 }}>folded</span>
                )}
              </div>

              {/* Stack & Actions */}
              <div style={{ fontFamily: MONO, fontSize: 12, color: "var(--vw-color-text-muted)", display: "flex", justifyContent: "space-between" }}>
                <span>stack: {player.stack}</span>
                {player.committed_round > 0 && <span>bet: {player.committed_round}</span>}
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
              
              {/* Betting Controls */}
              {isInteractiveBetting && onAction && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8, justifyContent: "center" }}>
                  <button 
                    style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "4px 8px", borderRadius: 4, cursor: "pointer", fontFamily: MONO, fontSize: 12 }}
                    onClick={() => onAction({ type: "fold" })}>Fold</button>
                  <button 
                    style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "4px 8px", borderRadius: 4, cursor: "pointer", fontFamily: MONO, fontSize: 12 }}
                    onClick={() => onAction({ type: "check" })}>Check</button>
                  <button 
                    style={{ background: "rgba(163, 230, 53, 0.2)", border: "1px solid var(--vw-color-accent)", color: "white", padding: "4px 8px", borderRadius: 4, cursor: "pointer", fontFamily: MONO, fontSize: 12 }}
                    onClick={() => onAction({ type: "call" })}>Call</button>
                  <div style={{ display: "flex", gap: 4 }}>
                    <input 
                      type="number" 
                      value={raiseAmount} 
                      onChange={e => setRaiseAmount(e.target.value)} 
                      style={{ width: 50, background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.1)", color: "white", padding: "2px 4px", borderRadius: 4, fontFamily: MONO, fontSize: 12 }}
                      placeholder="Amt"
                    />
                    <button 
                      style={{ background: "rgba(244, 63, 94, 0.2)", border: "1px solid var(--vw-color-danger)", color: "white", padding: "4px 8px", borderRadius: 4, cursor: "pointer", fontFamily: MONO, fontSize: 12 }}
                      onClick={() => onAction({ type: "raise", to: parseInt(raiseAmount) || 0 })}>Raise</button>
                  </div>
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
