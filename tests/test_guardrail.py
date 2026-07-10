from harness.guardrail import guardrail, is_within_sandbox, HitlState, Decision
from harness.actions import EditFile, RunShell, ReadFile, RunTests, Finish
from harness.config import load_config

cfg = load_config({"sandbox_root": "/sandbox"})


def test_blocks_rm_rf():
    d = guardrail(RunShell("rm -rf /"), cfg)
    assert d.kind == "Deny" and "rm -rf" in d.reason


def test_blocks_escape_edit():
    d = guardrail(EditFile("/etc/passwd", "x", "y"), cfg)
    assert d.kind == "Deny"


def test_allows_in_sandbox():
    assert guardrail(EditFile("/sandbox/a.py", "x", "y"), cfg).kind == "Allow"
    assert guardrail(ReadFile("/sandbox/a.py"), cfg).kind == "Allow"
    assert guardrail(RunTests("tests/"), cfg).kind == "Allow"
    assert guardrail(Finish(), cfg).kind == "Allow"


def test_warnlist_requires_approval():
    cfg2 = load_config({"sandbox_root": "/sandbox", "warnlist": ["git push"]})
    assert guardrail(RunShell("git push"), cfg2).kind == "RequireApproval"


def test_hitl_state_machine():
    h = HitlState()
    h.submit(RunShell("git push"))
    assert h.pending is not None
    h.decide(False)
    assert h.pending is None and h.last == "Denied"
