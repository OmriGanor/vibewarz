# @vibewarz/replay-viewer

React components for rendering [vibewarz](https://github.com/OmriGanor/vibewarz)
match replays from a JSONL event stream. This is the same renderer the
official platform's web UI uses — extracted into a standalone package so the
Python CLI (`vibewarz replay --watch`) and any third-party tool can render
replays through the same code.

> **0.x is unstable.** Expect breaking changes between minor versions until
> 1.0.

## Status

| Game  | Renderer | Notes                                              |
| ----- | -------- | -------------------------------------------------- |
| Curve | ✅        | `CurveReplay`                                      |
| Blast | ❌        | Pending decoupling from the live-game board.       |
| Poker | ❌        | Pending decoupling from the live-game board.       |

## Install

```bash
pnpm add @vibewarz/replay-viewer react react-dom
```

`react` and `react-dom` are peer dependencies (≥18).

## Use

```tsx
import { CurveReplay } from "@vibewarz/replay-viewer";
import "@vibewarz/replay-viewer/styles.css";

export function Replay({ events }) {
  return <CurveReplay events={events} />;
}
```

The `events` prop is the `events` array from a replay envelope:

```ts
type ReplayEnvelope = {
  match_id: string;
  game_id?: string;
  events: RawEvent[]; // GameStart | TickResult | GameEnd
};
```

— exactly the shape served by `GET /api/replays/{match_id}` from the
vibewarz platform, or by `vibewarz replay --watch` from the OSS CLI.

If you're loading from a generic JSONL file or unsure of the game, use
`detectGameId`:

```tsx
import { CurveReplay, detectGameId, type RawReplay } from "@vibewarz/replay-viewer";

function Replay({ replay }: { replay: RawReplay }) {
  const game = detectGameId(replay);
  if (game === "curve") return <CurveReplay events={replay.events} />;
  return <p>no renderer for {game ?? "(unknown)"} yet</p>;
}
```

## Theming

The component ships sensible dark-theme defaults. Override any of these CSS
custom properties on an ancestor element to re-skin:

```css
--vw-color-bg
--vw-color-surface
--vw-color-surface-2
--vw-color-border
--vw-color-text
--vw-color-text-muted
--vw-color-accent
--vw-color-danger
--vw-font-mono
--vw-radius
```

Example bridge from Tailwind theme tokens:

```tsx
<div
  style={{
    ["--vw-color-surface" as string]: "var(--color-surface)",
    ["--vw-color-text-muted" as string]: "var(--color-text-muted)",
    ["--vw-color-accent" as string]: "var(--color-accent)",
    ["--vw-color-danger" as string]: "var(--color-danger)",
  } as React.CSSProperties}
>
  <CurveReplay events={events} />
</div>
```

All component class names are prefixed `vw-replay__*` so the included
`styles.css` is safe to import alongside an app's own global CSS.

## Development

This package lives in the [vibewarz](https://github.com/OmriGanor/vibewarz)
monorepo. To iterate locally with a downstream consumer (e.g. the platform
web app) before publishing a release:

```bash
# In vibewarz-oss
pnpm install
pnpm -F @vibewarz/replay-viewer build

# In the consuming repo
pnpm add file:../vibewarz-oss/packages/replay-viewer
```

Publish via the `release-npm` workflow on merge to `main`; manual publishing
is not supported (see `.changeset/README.md`).
