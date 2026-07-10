import shutil
import pathlib
from fastapi.testclient import TestClient
from web.app import app, set_runtime
from harness.config import load_config
from harness.llm.mock import MockLLM


def test_post_task_runs_loop(tmp_path):
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp_path / "kata_assertion")
    cfg = load_config({"sandbox_root": str(tmp_path), "retry_budget": 3})
    llm = MockLLM(script=["EDIT kata_assertion/lib.py return a - b->return a + b", "TEST kata_assertion", "FINISH"])
    set_runtime(llm=llm, cfg=cfg)
    c = TestClient(app)
    r = c.post("/tasks", json={"kata": "kata_assertion"})
    assert r.status_code == 200 and r.json()["status"] == "done"
