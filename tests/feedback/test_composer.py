from harness.feedback.composer import compose, Feedback
from harness.feedback.parse import Failure
from harness.context import State


def test_compose_includes_failure_and_hint():
    fs = [Failure(file="a.py", line=2, assertion="assert 4==5", traceback="AssertionError")]
    fb = compose(fs, State(retry_budget=3, current_kata="k1"))
    assert isinstance(fb, Feedback)
    assert "a.py" in fb.text and "budget" in fb.text.lower()
    assert fb.failures and fb.retry_state["budget"] == 3
