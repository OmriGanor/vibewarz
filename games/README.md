# vibewarz-games

Pure-Python authoritative game engines for [vibewarz](https://vibewarz.com).

```bash
pip install vibewarz-games
```

Each game is a `Game` subclass with a pure `step(state, actions) -> StepResult`. Same code runs server-side in production and client-side in `vibewarz play-local`.

```python
from vibewarz_games import GAMES

curve = GAMES["curve"]()
state = curve.initial_state(seed=42, num_players=4)
result = curve.step(state, {0: {"turn": "LEFT"}, 1: {"turn": "STRAIGHT"}, 2: {}, 3: {}})
print(result.state)
```

## Games

| id | min/max players | description |
|---|---|---|
| [`curve`](../docs/games/curve.md) | 2/8 | Light-cycle / Achtung die Kurve — turn left/right/straight, don't hit walls or trails |
| [`poker`](../docs/games/poker.md) | 2/9 | Texas hold'em, no-limit tournament format |
| [`blast`](../docs/games/blast.md) | 2/4 | Drop bombs, dodge explosions, last bot standing wins |

Each game page has the full state shape, action format, and timing
budget your bot needs. The wire-format protocol that wraps them lives
in [PROTOCOL.md](../docs/PROTOCOL.md).

## License

MIT.
