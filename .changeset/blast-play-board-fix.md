---
"@vibewarz/game-ui": patch
---

blast: fix the live play board, which regressed when the replay aspect-ratio work made `BlastBoard` always pad itself to a square with a large meet-fit intrinsic size. That is correct inside the replay's fixed-ratio frame, but the play page renders the board directly into a flexible column, so it ballooned to the full column width, fell out of line with the side panels, and ran past the fold.

The square padding / large-intrinsic / meet-fit behaviour is now gated behind a new `frame` prop (which only `BlastReplay` sets). With `frame` off, the board renders at its natural rectangular size, capped to the container width, and centered (`margin-inline:auto`) — restoring the pre-replay play-page layout. The replay frame is unchanged.
