---
"@vibewarz/game-ui": minor
---

poker: on-table turn timer for the acting player. The board shows a countdown for the seat the action is on, anchored to the server deadline (`TickRequestS2C.deadline_ts`) for live play and falling back to a local countdown of `Poker.meta.tick_deadline_ms` (15s) when no deadline is supplied. Enters a danger state in the final 5 seconds and plays a per-second tick sound inside the last 10. Replays pass `turnTimer={null}` to disable it.
