---
"@vibewarz/game-ui": patch
---

replay: move the vibewarz mark to the left and add the brand icon. Both wordmarks (the in-frame board corner and the playback-controls bar) now sit on the LEFT instead of the right, each prefixed with the vibewarz icon — a green rounded bar rendered as a CSS `::before` on `.vw-replay__wordmark` (pure shape, themeable via `--vw-color-accent`, no asset). The board-corner mark groups with the winner badge (`▍vibewarz 🏆 name`); in the tall 9:16 frame it's lifted off the bottom edge so it stays noticeable.
