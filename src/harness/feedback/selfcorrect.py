from harness.context import State
from harness.feedback.parse import Failure
from harness.feedback.classifier import classify


def update_state(state: State, failures: list) -> str:
    if not failures:
        state.status = "done"
        return "done"
    if state.retry_budget <= 0:
        state.status = "aborted"
        return "aborted"
    state.retry_budget -= 1
    # if budget exhausted with failures remaining → abort
    if state.retry_budget <= 0:
        state.status = "aborted"
        return "aborted"
    # track repeated failure types
    ftypes = [classify(f)[0] for f in failures]
    state._repeat_counts = getattr(state, "_repeat_counts", {})
    escalated = False
    for t in ftypes:
        state._repeat_counts[t] = state._repeat_counts.get(t, 0) + 1
        if state._repeat_counts[t] >= 3:
            escalated = True
    state.escalated = escalated
    state.status = "running"
    return "running"
