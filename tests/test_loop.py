import shutil
import pathlib
from harness.loop import run
from harness.llm.mock import MockLLM
from harness.config import load_config


def _seed_arena(tmp):
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp / "kata_assertion")


def test_loop_self_corrects_to_green(tmp_path):
    _seed_arena(tmp_path)
    cfg = load_config({"sandbox_root": str(tmp_path), "retry_budget": 3})
    # turn1: wrong fix (multiply), turn2: correct fix (add), turn3: test, turn4: finish
    llm = MockLLM(script=[
        "EDIT kata_assertion/lib.py return a - b->return a * b",
        "EDIT kata_assertion/lib.py return a * b->return a + b",
        "TEST kata_assertion",
        "FINISH",
    ])
    out = run("kata_assertion", llm, cfg)
    assert out.status == "done"
    assert out.final_test_result.exit_code == 0


def test_loop_aborts_on_budget_exhaustion(tmp_path):
    _seed_arena(tmp_path)
    cfg = load_config({"sandbox_root": str(tmp_path), "retry_budget": 1})
    llm = MockLLM(script=["EDIT kata_assertion/lib.py return a - b->return a * b", "TEST kata_assertion"])
    out = run("kata_assertion", llm, cfg)
    assert out.status == "aborted"
