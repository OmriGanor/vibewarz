---
"@vibewarz/game-ui": minor
---

Curve replays go social-media-native at 1:1. `CurveReplay` now renders its square board inside the shared `ReplayFrame` (native 1:1) with the `AspectSelect` switcher in the playback controls, so a replay can be re-framed to 16:9 / 9:16 for capture (the square board centers on a branded backdrop in those). The right-hand player-card sidebar is dropped; each living player's name now rides their curve head, pulsing very subtly in their seat color (a dead player has no head, so its label simply disappears — which is how alive/dead reads). `CurveReplay` gains optional `defaultRatio`/`ratios` props (default 1:1). The winner is shown in the frame's brand corner at game end.
