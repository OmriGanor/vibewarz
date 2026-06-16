# Five-O Poker

A single-deal, **2-player** game. Each player builds five 5-card poker hands
(columns); the player who wins the most columns head-to-head wins the game.
There is no betting and no chips — one full board is built and a single
showdown decides it.

- **Players:** exactly 2
- **Decision budget:** 15 s — miss it and the engine substitutes the first
  legal placement for you
- **Variant:** "one and done" five-hand build (no betting)

## How a deal plays

1. **Deal:** 5 cards are dealt face-up, one to each of your five columns.
2. **Pacing:** players alternate, drawing one card at a time
   (`state.current_drawn_card`) and placing it in a column. A card may only go
   in one of your **currently-shortest** columns, so the board fills
   level-by-level and the columns stay within one card of each other.
3. **Visibility:** the **4th card** of each column (index 3) is dealt
   face-down — redacted from your opponent's view until showdown (it shows as
   `"??"`). The 5th card is face-up.
4. **Showdown:** once both boards are full (25 cards each) the five columns are
   ranked head-to-head. Winning the most columns takes the game; winning all
   five is a "Five-O" scoop. An equal number of columns won is a draw.

## Actions

When it is your seat's turn (`state["action_on"] == self.seat`), return a
single placement of the drawn card into one of the legal columns:

```python
{"type": "place", "column": idx}   # idx in 0..4
```

A column is **legal** only when it is among your shortest columns and is not
already full (5 cards). Returning an illegal placement on the live server is
substituted with the first legal column locally and eliminates you on the
ranked server, so always pick from the legal set.

```python
me = next(p for p in state["players"] if p["seat"] == self.seat)
lengths = [len(col) for col in me["columns"]]
min_len = min(lengths)
legal_columns = [
    i for i, n in enumerate(lengths) if n == min_len and n < 5
]
```

## State shape

`state` is the view for your seat (the opponent's face-down cards are
redacted).

| Key | Meaning |
|---|---|
| `phase` | `"placing"` while building, `"done"` at showdown |
| `action_on` | seat that owes a placement (`None` on the final settle tick) |
| `current_drawn_card` | the card you must place this turn, e.g. `"As"` |
| `players` | list of `{seat, columns, last_action}` |
| `history` | every placement so far as `{seat, action}` |
| `placement` | final finish order, winner first (filled at showdown) |
| `winner` | winning seat, or `-1` on a draw (filled at showdown) |
| `showdown_hands` | at showdown: `{seat: [hand_string × 5]}`, else `None` |
| `winning_columns` | at showdown: `{seat: [column index, …]}`, else `None` |

Per-player in `state["players"][i]`:

| Key | Meaning |
|---|---|
| `columns` | five lists of cards; your own are full, the opponent's 4th card is `"??"` until showdown |
| `last_action` | their most recent `{type, column}` or `None` |

Cards are two-character strings: rank (`2-9`, `T`, `J`, `Q`, `K`, `A`) + suit
(`s`, `h`, `d`, `c`), e.g. `"Td"`, `"As"`.

## Hidden information

You see all of your own cards. Your opponent's face-down 4th card in each
column arrives as `"??"` until the showdown reveal — the server is
authoritative and is the only thing that ever sees both full boards mid-deal.

## Tips for a first bot

1. Always place from the legal (shortest, non-full) columns — see the snippet
   above.
2. Group cards by rank to build pairs/trips: prefer a legal column whose cards
   already share the drawn card's rank.
3. You're building five hands at once, so a card that's wasted in one column is
   a column you've conceded. Think about which columns you're trying to win.
