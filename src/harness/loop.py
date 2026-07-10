from dataclasses import dataclass
from harness.context import build_context, State
from harness.parser import parse
from harness.guardrail import guardrail
from harness.dispatcher import dispatch
from harness.feedback.pipeline import pipeline
from harness.config import Config
from harness.actions import ParseError, RunTests, Finish


@dataclass
class Outcome:
    status: str
    turns: int
    final_test_result: object = None


def run(task: str, llm, cfg: Config, max_turns: int = 20, on_event=None) -> Outcome:
    state = State(retry_budget=cfg.retry_budget, current_kata=task)
    final = None
    for turn in range(max_turns):
        msgs = build_context(state, cfg)
        resp = llm.complete(messages=msgs)
        action = parse(resp.content)
        if isinstance(action, ParseError):
            state.history.append(("tool", f"parse error: {action.msg}"))
            continue
        dec = guardrail(action, cfg)
        if dec.kind == "Deny":
            state.history.append(("tool", f"denied: {dec.reason}"))
            continue
        if dec.kind == "RequireApproval":
            state.history.append(("tool", f"needs approval (auto-denied): {dec.reason}"))
            continue
        result = dispatch(action, cfg)
        if on_event:
            on_event({"turn": turn, "action": repr(action), "result": result.out or result.err,
                       "feedback": state.last_feedback})
        if isinstance(action, RunTests):
            fb = pipeline(result.test_result, state)
            final = result.test_result
            state.history.append(("tool", fb.text))
            if state.status in ("done", "aborted"):
                return Outcome(state.status, turn + 1, final)
        elif isinstance(action, Finish):
            return Outcome("done", turn + 1, final)
        else:
            state.history.append(("tool", result.out or result.err))
    return Outcome("aborted", max_turns, final)
