import json
import shutil
import tempfile
import os
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from harness.loop import run
from harness.config import load_config
from harness.llm.deepseek import DeepSeekClient

app = FastAPI()
_runtime = {}


class TaskReq(BaseModel):
    kata: str


def set_runtime(*, llm, cfg):
    _runtime["llm"] = llm
    _runtime["cfg"] = cfg


@app.on_event("startup")
def init_runtime():
    """Auto-configure runtime on server start."""
    sandbox = os.path.join(tempfile.gettempdir(), "harness-sandbox")
    os.makedirs(sandbox, exist_ok=True)
    # Seed katas into sandbox on first run
    arena = os.path.join(os.path.dirname(os.path.dirname(__file__)), "arena")
    if os.path.isdir(arena):
        for kata in os.listdir(arena):
            src = os.path.join(arena, kata)
            dst = os.path.join(sandbox, kata)
            if os.path.isdir(src) and not os.path.exists(dst):
                shutil.copytree(src, dst)
    cfg = load_config({"sandbox_root": sandbox, "retry_budget": 5})
    _runtime["cfg"] = cfg
    try:
        _runtime["llm"] = DeepSeekClient(model="deepseek-chat")
    except Exception:
        from harness.llm.mock import MockLLM
        _runtime["llm"] = MockLLM(script=["EDIT lib.py a - b->a + b", "TEST .", "FINISH"])


@app.post("/tasks")
def post_tasks(req: TaskReq):
    out = run(req.kata, _runtime["llm"], _runtime["cfg"])
    return {"status": out.status, "turns": out.turns}


@app.websocket("/stream")
async def stream_endpoint(ws: WebSocket):
    kata = ws.query_params.get("kata", "kata_assertion")
    await ws.accept()
    llm = _runtime["llm"]
    cfg = _runtime["cfg"]

    events = []

    out = await run_in_threadpool(
        run, kata, llm, cfg, 20,
        lambda e: events.append(e),
    )

    for e in events:
        await ws.send_text(json.dumps(e, default=str))

    await ws.send_text(json.dumps({"status": out.status, "turns": out.turns}, default=str))
