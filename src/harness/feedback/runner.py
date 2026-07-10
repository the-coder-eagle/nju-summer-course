import subprocess
from dataclasses import dataclass, field
from harness.config import Config


@dataclass
class TestResult:
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
