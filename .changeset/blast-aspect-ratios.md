---
"@vibewarz/game-ui": minor
---

Blast replays go social-media-native at 1:1. The 13×11 board is padded to a true square (the grid is centered with an invisible same-color matte) so it renders natively at 1:1 inside the shared `ReplayFrame`, with the `AspectSelect` switcher in the playback controls — a replay can be re-framed to 16:9 / 9:16 for capture (the square board centers on a branded backdrop). The right-hand sidebar and the below-board HUD (and the per-player B/R/S powerup stats) are dropped for a clean clip: in native 1:1 each living player's name rides their character; in 16:9 / 9:16 identity moves to a roster legend (chip + name, dead dimmed) centered in the letterbox dead-space band. `BlastReplay` gains optional `defaultRatio`/`ratios` props (default 1:1); the winner shows in the frame's brand corner at game end.
