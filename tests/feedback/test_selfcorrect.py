from harness.feedback.selfcorrect import update_state
from harness.context import State
from harness.feedback.parse import Failure


def test_no_failures_done():
    assert update_state(State(retry_budget=2), []) == "done"


def test_budget_zero_aborted():
    s = State(retry_budget=0)
    assert update_state(s, [Failure(file="a", traceback="AssertionError")]) == "aborted"


def test_escalation_after_repeats():
    s = State(retry_budget=4, current_kata="k")
    for _ in range(3):
        st = update_state(s, [Failure(file="a", traceback="AssertionError", assertion="x==y")])
    assert st == "running"
    assert s.escalated is True
