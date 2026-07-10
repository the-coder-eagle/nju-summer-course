import subprocess
from dataclasses import dataclass, field
from harness.config import Config


@dataclass
class TestResult:
    __test__ = False  # prevent pytest from collecting this as a test class
    exit_code: int
    stdout: str
    signals: dict = field(default_factory=dict)


def run_tests(target: str, cfg: Config, timeout: int = 30) -> TestResult:
    proc = subprocess.run(
        ["python", "-m", "pytest", "-q", "--no-header", target],
        cwd=cfg.sandbox_root, capture_output=True, text=True, timeout=timeout,
    )
    return TestResult(exit_code=proc.returncode, stdout=proc.stdout + proc.stderr,
                      signals={"pytest": proc.returncode})


def run_ruff(target: str, timeout: int = 15) -> TestResult:
    """Run ruff linter and return result. Non-zero exit means issues found."""
    try:
        proc = subprocess.run(
            ["ruff", "check", target, "--output-format=text"],
            capture_output=True, text=True, timeout=timeout,
        )
        return TestResult(exit_code=proc.returncode, stdout=proc.stdout + proc.stderr,
                          signals={"ruff": proc.returncode})
    except FileNotFoundError:
        return TestResult(exit_code=-1, stdout="ruff not installed",
                          signals={"ruff": -1})


def run_mypy(target: str, timeout: int = 15) -> TestResult:
    """Run mypy type checker and return result. Non-zero exit means issues found."""
    try:
        proc = subprocess.run(
            ["mypy", target, "--ignore-missing-imports"],
            capture_output=True, text=True, timeout=timeout,
        )
        return TestResult(exit_code=proc.returncode, stdout=proc.stdout + proc.stderr,
                          signals={"mypy": proc.returncode})
    except FileNotFoundError:
        return TestResult(exit_code=-1, stdout="mypy not installed",
                          signals={"mypy": -1})
