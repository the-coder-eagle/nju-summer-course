import json
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from harness.loop import run

app = FastAPI()
_runtime = {}


class TaskReq(BaseModel):
    kata: str


def set_runtime(*, llm, cfg):
    _runtime["llm"] = llm
    _runtime["cfg"] = cfg


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
