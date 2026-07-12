from harness.feedback.parse import parse_failures
from harness.feedback.runner import TestResult

SAMPLE = """FAILED kata_assertion/test_lib.py::test_add - assert (2-3) == 5
assert (2-3) == 5
 where (2-3) = -1
kata_assertion/lib.py:2: AssertionError"""


def test_parse_extracts_failure():
    fs = parse_failures(TestResult(1, SAMPLE))
    assert len(fs) == 1
    assert fs[0].file == "kata_assertion/test_lib.py"
    assert "assert" in fs[0].assertion


def test_parse_empty_when_passing():
    assert parse_failures(TestResult(0, "1 passed")) == []
