import shutil
import pathlib
from harness.feedback.runner import run_tests
from harness.config import load_config


def test_runner_reports_failure_for_buggy_kata(tmp_path):
    # copy kata_assertion fixture into sandbox
    src = pathlib.Path("arena/kata_assertion")
    shutil.copytree(src, tmp_path / "kata_assertion")
    cfg = load_config({"sandbox_root": str(tmp_path)})
    tr = run_tests("kata_assertion", cfg)
    assert tr.exit_code != 0
    assert "assert" in tr.stdout.lower() or "failed" in tr.stdout.lower()
