import shutil
import pathlib
import json
from web.app import app
from harness.config import load_config
from harness.llm.mock import MockLLM
from harness.loop import run


def test_on_event_callback_emits_turn_events(tmp_path):
    """Verify the on_event callback mechanism (core of WS streaming)."""
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp_path / "kata_assertion")
    cfg = load_config({"sandbox_root": str(tmp_path), "retry_budget": 3})
    llm = MockLLM(script=["EDIT kata_assertion/lib.py return a - b->return a + b", "TEST kata_assertion", "FINISH"])
    events = []
    out = run("kata_assertion", llm, cfg, on_event=lambda e: events.append(e))
    assert out.status == "done"
    assert any("action" in e for e in events)


def test_ws_route_registered():
    """Verify /stream WebSocket route exists."""
    routes = [r.path for r in app.routes]
    assert "/stream" in routes
