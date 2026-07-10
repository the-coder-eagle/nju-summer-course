"""§A.6 Mechanism Demos — all deterministic under MockLLM, no network."""
import shutil
import pathlib
from harness.guardrail import guardrail
from harness.actions import RunShell, EditFile
from harness.config import load_config
from harness.loop import run
from harness.llm.mock import MockLLM

cfg = load_config({"sandbox_root": "/sandbox"})


def test_demo1_guardrail_intercepts_dangerous_action():
    """① 治理护栏拦截危险动作"""
    assert guardrail(RunShell("rm -rf /"), cfg).kind == "Deny"
    assert guardrail(EditFile("/etc/passwd", "x", "y"), cfg).kind == "Deny"


def test_demo2_feedback_drives_self_correction(tmp_path):
    """② 注入失败→反馈→改下一步→绿"""
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp_path / "kata_assertion")
    c = load_config({"sandbox_root": str(tmp_path), "retry_budget": 3})
    llm = MockLLM(script=[
        "EDIT kata_assertion/lib.py return a - b->return a * b",
        "EDIT kata_assertion/lib.py return a * b->return a + b",
        "TEST kata_assertion", "FINISH",
    ])
    out = run("kata_assertion", llm, c)
    assert out.status == "done" and out.final_test_result.exit_code == 0


def test_demo3_classifier_and_budget_abort(tmp_path):
    """③ 分类器 + 预算耗尽 → abort"""
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp_path / "kata_assertion")
    c = load_config({"sandbox_root": str(tmp_path), "retry_budget": 1})
    llm = MockLLM(script=["EDIT kata_assertion/lib.py return a - b->return a * b", "TEST kata_assertion"])
    out = run("kata_assertion", llm, c)
    assert out.status == "aborted"
