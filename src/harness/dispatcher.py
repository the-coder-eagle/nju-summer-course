import os
import subprocess
from dataclasses import dataclass, field
from harness.actions import ReadFile, EditFile, RunShell, RunTests, Finish
from harness.config import Config


@dataclass
class ActionResult:
    ok: bool
    out: str = ""
    err: str = ""
    changed_files: list = field(default_factory=list)
    test_result: object = None


def _sandbox_path(path, root):
    return os.path.realpath(os.path.join(root, path)) if not os.path.isabs(path) else os.path.realpath(path)


def dispatch(action, cfg: Config, test_runner=None):
    if isinstance(action, ReadFile):
        p = _sandbox_path(action.path, cfg.sandbox_root)
        try:
            return ActionResult(ok=True, out=open(p, encoding="utf-8").read())
        except OSError as e:
            return ActionResult(ok=False, err=str(e))
    if isinstance(action, EditFile):
        p = _sandbox_path(action.path, cfg.sandbox_root)
        try:
            text = open(p, encoding="utf-8").read()
            text = text.replace(action.old, action.new)
            open(p, "w", encoding="utf-8").write(text)
            return ActionResult(ok=True, changed_files=[p])
        except OSError as e:
            return ActionResult(ok=False, err=str(e))
    if isinstance(action, RunShell):
        proc = subprocess.run(action.cmd, shell=True, cwd=cfg.sandbox_root,
                              capture_output=True, text=True, timeout=30)
        return ActionResult(ok=(proc.returncode == 0), out=proc.stdout, err=proc.stderr)
    if isinstance(action, RunTests):
        runner = test_runner
        if runner is None:
            from harness.feedback.runner import run_tests  # lazy
            runner = run_tests
        tr = runner(action.target, cfg)
        return ActionResult(ok=(tr.exit_code == 0), out=tr.stdout, test_result=tr)
    if isinstance(action, Finish):
        return ActionResult(ok=True, out="finished")
    return ActionResult(ok=False, err=f"unknown action {action}")
