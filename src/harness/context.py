from dataclasses import dataclass, field
from harness.actions import Message
from harness.memory import load_conventions
from harness.config import Config

SYSTEM_PROMPT = (
    "You are a coding agent harness. Repair failing tests in the sandbox. "
    "Emit exactly one action per turn: EDIT <path> <old>-><new>, READ <path>, "
    "SHELL <cmd>, TEST <target>, or FINISH. Do not edit outside the sandbox."
)


@dataclass
class State:
    history: list = field(default_factory=list)          # list[(role, content)]
    retry_budget: int = 5
    status: str = "running"                              # running|done|aborted
    current_kata: str = ""
    last_feedback: str = ""
    escalated: bool = False


def build_context(state: State, cfg: Config) -> list:
    conv = load_conventions(cfg.sandbox_root)
    msgs = [Message("system", SYSTEM_PROMPT + ("\n\nConventions:\n" + conv if conv else ""))]
    msgs.append(Message("user", f"Repair failing tests in kata: {state.current_kata}"))
    for role, content in state.history:
        msgs.append(Message(role, content))
    if state.last_feedback:
        msgs.append(Message("tool", state.last_feedback))
    return msgs
