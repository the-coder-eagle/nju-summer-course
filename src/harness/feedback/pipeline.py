from harness.feedback.runner import TestResult
from harness.feedback.parse import parse_failures
from harness.feedback.composer import compose
from harness.feedback.selfcorrect import update_state
from harness.context import State


def pipeline(tr: TestResult, state: State):
    failures = parse_failures(tr)
    status = update_state(state, failures)
    fb = compose(failures, state)
    state.last_feedback = fb.text
    return fb
