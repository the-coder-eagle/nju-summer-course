import os
from dataclasses import dataclass, field
from harness.actions import Message
from harness.memory import load_conventions
from harness.config import Config

SYSTEM_PROMPT = (
    "You are a coding agent that repairs failing Python tests. "
    "You can READ files, EDIT files (replace 'old' with 'new'), run SHELL commands, "
    "run TEST (pytest), or FINISH when tests pass.\n\n"
    "Emit exactly ONE action per turn in the following format:\n"
    "  EDIT <filepath> <old_code>-><new_code>\n"
    "  READ <filepath>\n"
    "  SHELL <command>\n"
    "  TEST <target>\n"
    "  FINISH\n\n"
    "The sandbox contains a kata with a buggy lib.py and a failing test_lib.py. "
    "Your job: make test_lib.py pass by editing lib.py."
)


@dataclass
class State:
    history: list = field(default_factory=list)          # list[(role, content)]
    retry_budget: int = 5
    status: str = "running"                              # running|done|aborted
    current_kata: str = ""
    last_feedback: str = ""
    escalated: bool = False


def _read_kata_files(sandbox_root: str, kata: str) -> str:
    """Read lib.py and test_lib.py from the kata directory."""
    lines = []
    kata_dir = os.path.join(sandbox_root, kata)
    for fname in ["lib.py", "test_lib.py", "CONVENTIONS.md"]:
        fpath = os.path.join(kata_dir, fname)
        if os.path.isfile(fpath):
            # Show relative path from sandbox root so agent knows the correct path
            rel = os.path.join(kata, fname).replace("\\", "/")
            lines.append(f"=== {rel} ===")
            with open(fpath, encoding="utf-8") as f:
                lines.append(f.read())
    return "\n".join(lines)


def build_context(state: State, cfg: Config) -> list:
    conv = load_conventions(cfg.sandbox_root)
    msgs = [Message("system", SYSTEM_PROMPT + ("\n\nConventions:\n" + conv if conv else ""))]

    # First turn: include actual kata file contents
    if not state.history:
        files = _read_kata_files(cfg.sandbox_root, state.current_kata)
        task = (f"Repair failing tests in kata: {state.current_kata}\n\n"
                f"Here are the files in the sandbox:\n\n{files}\n\n"
                f"Fix the bug in {state.current_kata}/lib.py, then run:\n"
                f"  TEST {state.current_kata}\n"
                f"When tests pass, reply FINISH.")
        msgs.append(Message("user", task))
    else:
        msgs.append(Message("user", f"Continue repairing kata: {state.current_kata}"))

    for role, content in state.history:
        msgs.append(Message(role, content))
    if state.last_feedback:
        msgs.append(Message("user", state.last_feedback))
    return msgs
