---
"@vibewarz/game-ui": minor
---

Curve replays go social-media-native at 1:1. `CurveReplay` now renders its square board inside the shared `ReplayFrame` (native 1:1) with the `AspectSelect` switcher in the playback controls, so a replay can be re-framed to 16:9 / 9:16 for capture (the square board centers on a branded backdrop in those). The right-hand player-card sidebar is dropped; in native 1:1 each living player's name rides their curve head, pulsing very subtly in their seat color (a dead player has no head, so its label simply disappears — which is how alive/dead reads). `CurveReplay` gains optional `defaultRatio`/`ratios` props (default 1:1). The winner is shown in the frame's brand corner at game end.

`ReplayFrame` also gains an optional `legend` prop: when a board is re-framed off its native ratio, the letterbox dead space is filled with a roster legend (color chip + name; dead players dimmed/struck-through). It's placed where social-video attention/safe-zones favor it — the left band when the frame is wider than native (pillarbox), the top band when it's taller (the bottom is the platform caption/action clutter zone). Curve uses this in 16:9 / 9:16 instead of on-head names.
