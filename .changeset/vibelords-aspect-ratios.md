---
"@vibewarz/game-ui": minor
---

Make replays social-media-shareable with selectable aspect ratios. Adds a shared `ReplayFrame` + `AspectSelect` (9:16 / 16:9 / 1:1) and renders the Vibelords board natively at 16:9 (the lane fills the clip, with a branded backdrop when re-framed). `VibelordsReplay` gains optional `defaultRatio`/`ratios` props (default 16:9) and drops its sidebar player cards — names, resources and base HP already read from the in-board HUD/keeps. The aspect selector sits in the playback controls; the framed region is a clean, branded rectangle for screen capture.
