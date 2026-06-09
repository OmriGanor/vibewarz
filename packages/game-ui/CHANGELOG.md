# @vibewarz/game-ui

## 0.3.0

### Minor Changes

- b1b7db1: Make replays social-media-shareable with selectable aspect ratios. Adds a shared `ReplayFrame` + `AspectSelect` (9:16 / 16:9 / 1:1) and renders the Vibelords board natively at 16:9 (the lane fills the clip, with a branded backdrop when re-framed). Units and keeps render substantially larger (1.8x) to fill the taller field and read better in clips, with each base's HP bar floating just above its own keep silhouette at any age. `VibelordsReplay` gains optional `defaultRatio`/`ratios` props (default 16:9) and drops its sidebar player cards — names, resources and base HP already read from the in-board HUD/keeps. The aspect selector sits in the playback controls; the framed region is a clean, branded rectangle for screen capture.

## 0.2.16

### Patch Changes

- 8ccae2a: Label players by `game_start.names` when the replay carries them (fallback: "seat N"); add a subtle vibewarz wordmark to the playback controls bar.

## 0.2.15

### Patch Changes

- 1876e4c: Add the Vibelords lane-RTS renderer — board, replay viewer, and asset sheet — plus `detectGameId` support for the `vibelords` game.

## 0.2.0

### Minor Changes

- 496273c: game-ui: identify the local player ("YOU") by consistent seat color instead of
  a separate marker. `BlastReplay` and `CurveReplay` now accept an optional
  `mySeat` prop — when set, the viewer's seat row (and the Blast HUD card) is
  tinted with that seat's color so "this is me" reads from color alone. Removes
  the faint Blast "this is you" halo and the muted lowercase "you" HUD label in
  favor of pure color matching. Spectator views (`mySeat` omitted / null) render
  unchanged.

## 0.1.0

### Minor Changes

- d294341: Initial release of `@vibewarz/game-ui` — React components for rendering
  vibewarz games. Includes replay viewers for all three games (`CurveReplay`,
  `BlastReplay`, `PokerReplay`) plus the shared presentational boards
  (`BlastBoard`, `PokerBoard`, `Card`, `ChipStack`, …) used by both replays and
  the platform's live-play UI. Extracted from the closed-source `apps/web` so the
  OSS Python CLI's `vibewarz replay --watch`, the platform replay pages, and the
  platform live-play pages all render through one source of truth. API is
  unstable in 0.x; expect breaking changes between minor versions until 1.0.
