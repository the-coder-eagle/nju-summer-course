from dataclasses import dataclass, field
from harness.feedback.classifier import classify
from harness.context import State


@dataclass
class Feedback:
    text: str
    failures: list
    retry_state: dict = field(default_factory=dict)


def compose(failures: list, state: State) -> Feedback:
    lines = [f"Feedback (retry budget left: {state.retry_budget}):"]
    for f in failures:
        ftype, hint = classify(f)
        f.type = ftype
        f.hint = hint
        lines.append(f"- {f.file}:{f.line or '?'} [{ftype}] {f.assertion or ''}\n  hint: {hint}")
    if not failures:
        lines.append("All tests passed.")
    return Feedback(text="\n".join(lines), failures=failures,
                    retry_state={"budget": state.retry_budget, "status": state.status})
