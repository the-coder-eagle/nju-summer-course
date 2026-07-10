import os
from dataclasses import dataclass, field
from harness.actions import Message
from harness.memory import load_conventions
from harness.config import Config

SYSTEM_PROMPT = """You are a bug-fixing agent. Your ONLY output each turn must be ONE of:

EDIT <path> <old_code>-><new_code>
READ <path>
SHELL <command>
TEST <target>
FINISH

No explanations. No markdown. No multiple actions. Just the command."""


@dataclass
class State:
    history: list = field(default_factory=list)          # list[(role, content)]
    retry_budget: int = 5
    status: str = "running"                              # running|done|aborted
    current_kata: str = ""
    last_feedback: str = ""
    escalated: bool = False


def _read_kata_files(sandbox_root: str, kata: str) -> str:
    """Read kata source and test files, return them with their paths."""
    lines = []
    # Determine the actual kata directory on disk
    if kata == ".":
        kata_dir = sandbox_root
        prefix = ""
    else:
        kata_dir = os.path.join(sandbox_root, kata)
        prefix = kata.replace("\\", "/") + "/"

    for fname in ["lib.py", "test_lib.py", "CONVENTIONS.md"]:
        fpath = os.path.join(kata_dir, fname)
        if os.path.isfile(fpath):
            lines.append(f"=== {prefix}{fname} ===")
            with open(fpath, encoding="utf-8") as f:
                lines.append(f.read())
    return "\n".join(lines)


def _test_target(state: State) -> str:
    """Return the correct TEST target for the current kata."""
    if state.current_kata == ".":
        return "TEST ."
    return f"TEST {state.current_kata}"


def build_context(state: State, cfg: Config) -> list:
    conv = load_conventions(cfg.sandbox_root)
    msgs = [Message("system", SYSTEM_PROMPT + ("\nConventions: " + conv if conv else ""))]

    if not state.history:
        files = _read_kata_files(cfg.sandbox_root, state.current_kata)
        task = (
            f"Kata: {state.current_kata}\n\n"
            f"{files}\n\n"
            f"1. EDIT the buggy file to fix the failing test\n"
            f"2. Run: {_test_target(state)}\n"
            f"3. If tests pass, reply: FINISH"
        )
        msgs.append(Message("user", task))
    else:
        last = _test_target(state)
        msgs.append(Message("user", f"Continue. To run tests use: {last}"))

    for role, content in state.history:
        msgs.append(Message(role, content))
    if state.last_feedback:
        msgs.append(Message("user", state.last_feedback))
    return msgs
