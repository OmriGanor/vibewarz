// Visual primitives: a stack of betting chips with a label, a tiny
// dealer-button disc, and a denomination-broken-down chip pile whose drawn
// chip count is proportional to the actual amount. These are the at-table
// indicators; they sit in front of each seat (chips) or beside the
// button-holder (dealer disc).

import type { CSSProperties } from "react";

const MONO = "ui-monospace, 'JetBrains Mono', Menlo, Consolas, monospace";

// Poker chip denominations, high→low, each with a felt-friendly color. An
// amount is broken down greedily into these (real-casino style), so the number
// of chips drawn scales with the actual amount instead of being a fixed glyph.
const DENOMS: { value: number; color: string }[] = [
  { value: 1000, color: "#dc2626" }, // red
  { value: 500, color: "#a855f7" }, // purple
  { value: 100, color: "#111827" }, // black
  { value: 25, color: "#10b981" }, // green
  { value: 5, color: "#3b82f6" }, // blue
  { value: 1, color: "#e5e7eb" }, // white
];

// Greedy denomination breakdown → one column per denomination present, capped
// to the `maxCols` most-significant denominations and `maxPerCol` chips each so
// a huge pot stays readable (the numeric label carries the exact value). The
// drawn height is still proportional to magnitude because larger amounts climb
// into higher denominations.
export function chipColumns(
  amount: number,
  maxCols = 3,
  maxPerCol = 6,
): { color: string; count: number }[] {
  const cols: { color: string; count: number }[] = [];
  let rem = Math.max(0, Math.floor(amount));
  for (const d of DENOMS) {
    if (rem < d.value) continue;
    const count = Math.floor(rem / d.value);
    rem -= count * d.value;
    cols.push({ color: d.color, count: Math.min(count, maxPerCol) });
  }
  if (cols.length === 0 && amount > 0) {
    cols.push({ color: DENOMS[DENOMS.length - 1].color, count: 1 });
  }
  return cols.slice(0, maxCols);
}

// A pile of chips drawn as side-by-side denomination columns of stacked discs.
// `unit` is the disc diameter in px. Purely presentational — the exact value
// is shown by the caller's label.
export function ChipPile({
  amount,
  unit = 14,
  maxCols = 3,
  maxPerCol = 6,
}: {
  amount: number;
  unit?: number;
  maxCols?: number;
  maxPerCol?: number;
}) {
  if (amount <= 0) return null;
  const cols = chipColumns(amount, maxCols, maxPerCol);
  const discH = Math.round(unit * 0.42); // a chip seen nearly edge-on
  const peek = Math.max(2, Math.round(unit * 0.26)); // visible sliver per stacked chip
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: Math.round(unit * 0.3) }}>
      {cols.map((c, ci) => (
        // Each column is a stack: chips absolutely positioned, each `peek` px
        // higher than the one below, so they overlap like real chips.
        <div
          key={ci}
          style={{ position: "relative", width: unit, height: discH + (c.count - 1) * peek }}
        >
          {Array.from({ length: c.count }).map((_, i) => (
            <span
              key={i}
              style={{
                position: "absolute",
                left: 0,
                bottom: i * peek,
                width: unit,
                height: discH,
                borderRadius: "50%",
                background: `radial-gradient(circle at 50% 35%, ${c.color}, ${c.color}bb)`,
                border: "1px solid rgba(255,255,255,0.7)",
                boxShadow: "0 1px 2px rgba(0,0,0,0.5)",
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export function ChipStack({ amount }: { amount: number }) {
  if (amount <= 0) return null;
  // Pick a chip color by denomination, mostly cosmetic.
  const tier =
    amount >= 500 ? "#dc2626" : amount >= 100 ? "#10b981" : amount >= 25 ? "#3b82f6" : "#f59e0b";
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontFamily: MONO,
        fontSize: 12,
        background: "rgba(0,0,0,0.45)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 999,
        padding: "2px 8px 2px 4px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.4)",
      }}
    >
      <span
        style={{
          width: 14,
          height: 14,
          borderRadius: 999,
          background: `radial-gradient(circle at 30% 30%, ${tier}, ${tier}aa)`,
          border: `1.5px dashed rgba(255,255,255,0.85)`,
          boxShadow: "0 0 0 1px rgba(0,0,0,0.5)",
        }}
      />
      <span style={{ color: "#fff" }}>{amount}</span>
    </div>
  );
}

export function DealerButton() {
  return (
    <div
      title="dealer"
      style={{
        width: 22,
        height: 22,
        borderRadius: 999,
        background: "radial-gradient(circle at 30% 30%, #ffffff, #d4d4d4)",
        color: "#0a0a0b",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: MONO,
        fontSize: 11,
        fontWeight: 800,
        border: "1px solid #525252",
        boxShadow: "0 2px 4px rgba(0,0,0,0.6)",
      }}
    >
      D
    </div>
  );
}
