import os
from dataclasses import dataclass
from harness.actions import EditFile, ReadFile, RunShell, RunTests, Finish
from harness.config import Config


@dataclass
class Decision:
    kind: str   # Allow | Deny | RequireApproval
    reason: str = ""


def is_within_sandbox(path: str, root: str) -> bool:
    root_abs = os.path.realpath(root)
    p = os.path.realpath(os.path.join(root, path)) if not os.path.isabs(path) else os.path.realpath(path)
    return os.path.commonpath([root_abs, p]) == root_abs


def guardrail(action, cfg: Config) -> Decision:
    if isinstance(action, (ReadFile, RunTests, Finish)):
        return Decision("Allow")
    if isinstance(action, EditFile):
        if not is_within_sandbox(action.path, cfg.sandbox_root):
            return Decision("Deny", f"edit outside sandbox: {action.path}")
        return Decision("Allow")
    if isinstance(action, RunShell):
        for d in cfg.denylist:
            if d in action.cmd:
                return Decision("Deny", f"denylisted: {d}")
        for w in cfg.warnlist:
            if w in action.cmd:
                return Decision("RequireApproval", f"warnlisted: {w}")
        return Decision("Allow")
    return Decision("Deny", f"unknown action: {action}")


class HitlState:
    def __init__(self):
        self.pending = None
        self.last = None

    def submit(self, action):
        self.pending = action
        self.last = None

    def decide(self, approved: bool):
        self.last = "Approved" if approved else "Denied"
        self.pending = None
        return self.last
