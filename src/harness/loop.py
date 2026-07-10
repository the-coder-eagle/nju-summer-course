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
            hint = ("Parse error: your response must be one of:\n"
                    "  EDIT <path> <old_code>-><new_code>\n"
                    "  READ <path>\n  SHELL <command>\n  TEST <target>\n  FINISH\n"
                    f"Got: {resp.content[:100]}")
            state.history.append(("user", hint))
            continue
        dec = guardrail(action, cfg)
        if dec.kind == "Deny":
            state.history.append(("user", f"denied: {dec.reason}"))
            continue
        if dec.kind == "RequireApproval":
            state.history.append(("user", f"needs approval (auto-denied): {dec.reason}"))
            continue
        result = dispatch(action, cfg)
        if on_event:
            on_event({"turn": turn, "action": repr(action), "result": result.out or result.err,
                       "feedback": state.last_feedback})
        if isinstance(action, RunTests):
            fb = pipeline(result.test_result, state)
            final = result.test_result
            state.history.append(("user", fb.text))
            if state.status in ("done", "aborted"):
                return Outcome(state.status, turn + 1, final)
        elif isinstance(action, Finish):
            return Outcome("done", turn + 1, final)
        else:
            feedback = result.out or result.err
            # After EDIT/READ/SHELL success, hint what to do next
            from harness.actions import EditFile
            if result.ok and isinstance(action, EditFile):
                feedback += (f"\nFile edited. Now reply with exactly:\n"
                             f"TEST {state.current_kata}")
            state.history.append(("user", feedback))
    return Outcome("aborted", max_turns, final)
