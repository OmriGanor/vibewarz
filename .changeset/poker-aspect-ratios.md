---
"@vibewarz/game-ui": minor
---

Poker replays go social-media-native at 16:9. `PokerReplay` renders the table inside the shared `ReplayFrame` with the `AspectSelect` switcher (alongside the existing POV dropdown), and passes real player names (`seatInfo`) so identity — name, stack, cards, status — lives on the table; the sidebar is dropped. The felt is a rounded-rectangle that fills the frame (header tucked in the top corners). In **9:16** the whole table spins 90° to fill the tall frame with cards/names counter-rotated upright and shrunk. In **1:1** the table centers with a stack leaderboard (chip + name + stack, sorted high→low, busted dimmed) in the letterbox bands. Picking a POV reveals/labels that seat without resizing it. `PokerReplay` gains optional `defaultRatio`/`ratios` (default 16:9); winner shown in the brand corner at game end.
