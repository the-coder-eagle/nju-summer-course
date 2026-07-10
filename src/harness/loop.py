from dataclasses import dataclass
from harness.context import build_context, State
from harness.parser import parse
from harness.guardrail import guardrail
from harness.dispatcher import dispatch
from harness.feedback.pipeline import pipeline
from harness.config import Config
from harness.actions import ParseError, RunTests, Finish, EditFile, ReadFile, RunShell


@dataclass
class Outcome:
    status: str
    turns: int
    final_test_result: object = None


def _test_cmd(state: State) -> str:
    """The correct TEST command for the current kata."""
    t = state.current_kata if state.current_kata != "." else "."
    return f"TEST {t}"


def run(task: str, llm, cfg: Config, max_turns: int = 20, on_event=None, logger=None) -> Outcome:
    state = State(retry_budget=cfg.retry_budget, current_kata=task)
    final = None
    for turn in range(max_turns):
        msgs = build_context(state, cfg)
        resp = llm.complete(messages=msgs)
        action = parse(resp.content)

        if isinstance(action, ParseError):
            state.history.append(("user",
                f"Invalid format. Reply with ONE of: EDIT <path> <old>-><new>, "
                f"READ <path>, SHELL <cmd>, {_test_cmd(state)}, FINISH"))
            continue

        dec = guardrail(action, cfg)
        if dec.kind == "Deny":
            state.history.append(("user", f"Denied: {dec.reason}. Use a safe alternative."))
            continue
        if dec.kind == "RequireApproval":
            state.history.append(("user", f"Needs approval: {dec.reason}. Try a different approach."))
            continue

        result = dispatch(action, cfg)
        if on_event:
            on_event({"turn": turn, "action": repr(action), "result": result.out or result.err,
                       "feedback": state.last_feedback})
        if logger:
            logger.log(turn, repr(action), result.out or result.err, state.last_feedback)

        if isinstance(action, RunTests):
            fb = pipeline(result.test_result, state)
            final = result.test_result
            state.history.append(("user", fb.text))
            if state.status in ("done", "aborted"):
                return Outcome(state.status, turn + 1, final)
        elif isinstance(action, Finish):
            return Outcome("done", turn + 1, final)
        elif isinstance(action, EditFile):
            if result.ok:
                state.history.append(("user",
                    f"Edit OK. Now run {_test_cmd(state)} to verify, then FINISH."))
            else:
                state.history.append(("user",
                    f"Edit FAILED: {result.err}. Check the file path and try again."))
        elif isinstance(action, ReadFile):
            if result.ok:
                state.history.append(("user",
                    f"Read OK:\n{result.out[:500]}\nNow fix the bug with EDIT, then run {_test_cmd(state)}."))
            else:
                state.history.append(("user",
                    f"Read FAILED: {result.err}. Try correct path: {state.current_kata}/<file>."))
        else:
            state.history.append(("user", result.out or result.err))

    return Outcome("aborted", max_turns, final)
