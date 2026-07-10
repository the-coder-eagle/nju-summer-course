from harness.feedback.pipeline import pipeline
from harness.feedback.runner import TestResult
from harness.context import State


def test_pipeline_classifies_and_updates_state():
    tr = TestResult(1, "FAILED a/test_x.py::test_t - assert 4==5\na/lib.py:2: AssertionError")
    s = State(retry_budget=3, current_kata="a")
    fb = pipeline(tr, s)
    assert "a/test_x.py" in fb.text
    assert s.retry_budget == 2          # decremented
    assert s.status == "running"


def test_pipeline_done_on_pass():
    s = State(retry_budget=3)
    fb = pipeline(TestResult(0, "1 passed"), s)
    assert s.status == "done" and "passed" in fb.text.lower()
