from harness.context import build_context, State
from harness.config import load_config


def test_context_has_system_task_history_feedback(tmp_path):
    cfg = load_config({"sandbox_root": str(tmp_path)})
    st = State(history=[("tool", "ran tests")], retry_budget=3, status="running", current_kata="k1")
    msgs = build_context(st, cfg)
    roles = [m.role for m in msgs]
    assert roles[0] == "system"
    assert any("k1" in m.content for m in msgs)
    assert any("ran tests" in m.content for m in msgs)
