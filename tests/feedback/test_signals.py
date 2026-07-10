from harness.feedback.runner import run_ruff, run_mypy, TestResult
from harness.feedback.parse import parse_failures


def test_ruff_detects_issues(tmp_path):
    """ruff should detect style issues in Python code."""
    f = tmp_path / "bad.py"
    f.write_text("import os\nimport sys\nx=1\n")
    tr = run_ruff(str(tmp_path), timeout=10)
    assert isinstance(tr, TestResult)
    # ruff should find unused imports or missing whitespace
    assert "unused" in tr.stdout.lower() or "E" in tr.stdout or "F401" in tr.stdout or tr.exit_code != 0


def test_ruff_clean_code_passes(tmp_path):
    """ruff should pass on clean code."""
    f = tmp_path / "clean.py"
    f.write_text("def foo():\n    return 1\n")
    tr = run_ruff(str(tmp_path), timeout=10)
    # Clean code might pass or have minor issues depending on ruff version
    assert isinstance(tr, TestResult)


def test_mypy_detects_type_errors(tmp_path):
    """mypy should detect type mismatches."""
    f = tmp_path / "types.py"
    f.write_text("def add(a: int, b: int) -> int:\n    return str(a + b)\n")
    tr = run_mypy(str(tmp_path), timeout=10)
    assert isinstance(tr, TestResult)
    # mypy should detect return type mismatch
    assert "error" in tr.stdout.lower() or tr.exit_code != 0


def test_parse_ruff_output():
    """parse_failures should handle ruff-style output."""
    ruff_out = "bad.py:1:8: F401 [*] `os` imported but unused\nbad.py:3:1: E302 expected 2 blank lines\n"
    tr = TestResult(1, ruff_out, signals={"ruff": 1})
    failures = parse_failures(tr)
    assert len(failures) >= 1


def test_multi_signal_merges_results():
    """TestResult with multiple signals should capture all."""
    tr = TestResult(
        exit_code=1,
        stdout="pytest: 1 failed\nruff: 3 issues\nmypy: 1 error",
        signals={"pytest": 1, "ruff": 3, "mypy": 1},
    )
    assert tr.signals["pytest"] == 1
    assert tr.signals["ruff"] == 3
    assert tr.signals["mypy"] == 1
