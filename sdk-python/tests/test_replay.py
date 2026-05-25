"""Client.fetch_replay() — happy path + 302→S3 redirect follow.

The server has two replay storage backends:
  - Local (dev): returns a JSON envelope inline.
  - S3 (prod): returns 302 to a presigned S3 URL.

httpx follows redirects transparently, so the SDK doesn't care which
backend served the response. Verify both paths via a mock transport.
"""

from __future__ import annotations

import httpx
import pytest
from vibewarz.client import Client
from vibewarz.protocol import GameStartEvt, ReplayEnvelope


def _envelope_json() -> dict:
    return {
        "match_id": "m_test",
        "game_id": "curve",
        "events": [
            {
                "type": "game_start",
                "seed": 42,
                "state": {"tick": 0, "players": []},
                "match_id": "m_test",
                "game_id": "curve",
            },
            {
                "type": "game_end",
                "ts": 1,
                "match_id": "m_test",
                "placement": [0, 1],
                "reason": "elimination",
                "final_state": {"tick": 10, "players": []},
            },
        ],
    }


@pytest.mark.asyncio
async def test_fetch_replay_inline_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = _envelope_json()

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/api/replays/m_test"
        return httpx.Response(200, json=expected)

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kw: real_client(transport=transport, **kw)
    )

    client = Client(url="wss://api.vibewarz.com/ws")
    env = await client.fetch_replay("m_test")
    assert isinstance(env, ReplayEnvelope)
    assert env.match_id == "m_test"
    assert env.game_id == "curve"
    assert len(env.events) == 2
    assert isinstance(env.events[0], GameStartEvt)


@pytest.mark.asyncio
async def test_fetch_replay_follows_302(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = _envelope_json()

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/api/replays/m_test":
            return httpx.Response(
                302,
                headers={"Location": "https://s3.example.com/replays/m_test.json"},
            )
        if req.url.host == "s3.example.com":
            return httpx.Response(200, json=expected)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kw: real_client(transport=transport, **kw)
    )

    client = Client(url="wss://api.vibewarz.com/ws")
    env = await client.fetch_replay("m_test")
    assert env.match_id == "m_test"
    assert env.game_id == "curve"


@pytest.mark.asyncio
async def test_fetch_replay_legacy_envelope_without_game_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replays written before envelope tagging shipped don't have
    `envelope.game_id`. The model should still parse — game_id is
    Optional — leaving recovery to viewers via state-shape inference."""
    payload = {
        "match_id": "m_legacy",
        "events": [
            {
                "type": "game_start",
                "seed": 1,
                "state": {},
                "match_id": "m_legacy",
            },
        ],
    }

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kw: real_client(transport=transport, **kw)
    )

    client = Client(url="ws://localhost:10000/ws")
    env = await client.fetch_replay("m_legacy")
    assert env.match_id == "m_legacy"
    assert env.game_id is None
