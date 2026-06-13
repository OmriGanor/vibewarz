"""Interactive UI runner.

Runs a local match where one seat is a UIHumanBot. 
Spins up an HTTP server that serves the compiled React viewer and endpoints for /state and /action.
"""

from __future__ import annotations

import importlib.resources as resources
import json
import random
import sys
import threading
import time
import uuid
import queue
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from vibewarz_games import GAMES, Game

from .bot import Bot
from .play_local import _load_bot_class, _ReplayJournal

_MIME = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
}

def _viewer_dist_root() -> Path:
    ref = resources.files("vibewarz").joinpath("viewer_dist")
    return Path(str(ref))


class UIHumanBot(Bot):
    def __init__(self, action_queue: queue.Queue, state_ref: dict):
        super().__init__()
        self.action_queue = action_queue
        self.state_ref = state_ref

    def act(self, state: dict) -> dict:
        self.state_ref["current"] = state
        action = self.action_queue.get()  # Block until UI POSTs an action
        self.state_ref["current"] = None
        return action


class UIServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            state = self.server.state_ref.get("current")
            if state:
                self.wfile.write(json.dumps(state).encode("utf-8"))
            else:
                self.wfile.write(b"null")
            return

        # Serve static viewer
        root = _viewer_dist_root()
        target = root / url.path.lstrip("/")
        if not target.exists() or target.is_dir():
            target = root / "index.html"
            
        mime = _MIME.get(target.suffix.lower(), "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        url = urlparse(self.path)
        if url.path == "/action":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                action = json.loads(body.decode("utf-8"))
                self.server.action_queue.put(action)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def _run_server(server: HTTPServer) -> None:
    server.serve_forever()


def play_ui(
    game_id: str,
    bot_path: Path,
    port: int = 8080,
    seed: int | None = None,
) -> None:
    if game_id not in GAMES:
        raise RuntimeError(f"unknown game {game_id!r}")
    game: Game = GAMES[game_id]()
    meta = game.meta

    action_queue = queue.Queue()
    state_ref = {"current": None}

    # Setup Server
    server = HTTPServer(("127.0.0.1", port), UIServerHandler)
    server.action_queue = action_queue
    server.state_ref = state_ref
    
    server_thread = threading.Thread(target=_run_server, args=(server,), daemon=True)
    server_thread.start()

    import webbrowser
    url = f"http://127.0.0.1:{port}/?live=1"
    print(f"UI Server running at {url}")
    print(f"Open your browser to play against {bot_path.name}!")
    webbrowser.open(url)

    # Setup Game
    bot_cls = _load_bot_class(bot_path)
    opponent = bot_cls()
    human = UIHumanBot(action_queue, state_ref)
    
    bots = [human, opponent]
    # Randomize seat? For now, human is seat 0
    human.seat = 0
    opponent.seat = 1

    for bot in bots:
        bot.match_id = "local_ui"
        bot.players = None

    seed = seed if seed is not None else random.randrange(2**31)
    state = game.initial_state(seed=seed, num_players=2)

    for bot in bots:
        initial_view = game.snapshot_view_for(state, bot.seat)
        bot.on_start(bot._coerce_state(initial_view))

    limit = meta.max_ticks
    tick = 0

    try:
        while tick < limit:
            actions: dict[int, dict] = {}
            for seat in game.acting_seats(state):
                view = game.view_for(state, seat)
                try:
                    out = bots[seat].act(bots[seat]._coerce_state(view))
                except Exception as e:
                    print(f"seat {seat} raised in act(): {e!r}", file=sys.stderr)
                    actions[seat] = game.default_action(state, seat)
                    continue
                action, _ = bots[seat]._normalize_action_output(out)
                if not isinstance(action, dict) or not game.is_legal(state, seat, action):
                    actions[seat] = game.default_action(state, seat)
                else:
                    actions[seat] = action

            result = game.step(state, actions)
            state = result.state
            tick += 1
            
            # Post final state so UI can render showdown
            if result.done:
                state_ref["current"] = game.journal_view(state)
                break
                
        print("Game Over!")
        for bot in bots:
            bot.on_end(result.placement or [], result.reason or "done")
            
        # Keep server alive so user can see final state
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        server.shutdown()
