# Coding Agent Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Homework gate (§4.5):** Before executing any task, run cold-start verification with a DIFFERENT agent type (fresh session, only SPEC.md + this PLAN.md). No implementation code before that passes.

**Goal:** Build a self-coded Coding Agent Harness kernel whose feedback loop deterministically repairs failing Python tests, with mock-LLM unit tests, a streaming WebUI, Docker distribution, and NJU GitLab CI.

**Architecture:** Thin main loop orchestrates typed actions through a guardrail and dispatcher; on `RunTests` a pure-function feedback pipeline (Run→Parse→Classify→Compose→SelfCorrect) feeds structured failures back into context. LLM is an injectable OpenAI-compatible abstraction (DeepSeek real, Mock for tests). WebUI is a thin adapter over the loop; the kernel imports no web framework.

**Tech Stack:** Python 3.11+, pytest, httpx (OpenAI-compatible calls), keyring (Windows Credential Manager), FastAPI/uvicorn (WebUI), Docker, NJU GitLab CI.

## Global Constraints

- Python ≥ 3.10 (dev machine default is 3.10.11; no 3.11-only features used; 3.11–3.13 also fine). Pin `pytest>=8,<9`, `httpx>=0.27`, `keyring>=25`, `fastapi>=0.110`, `uvicorn>=0.29`, `ruff>=0.6`, `mypy>=1.11`.
- No high-level agent frameworks (LangChain AgentExecutor / AutoGen / CrewAI / LlamaIndex agent) — §A.4-A.
- Mechanisms are code, not prompts — §A.4-B. Every core mechanism must pass a deterministic unit test under Mock/stub LLM with no network — §A.4-C.
- Six dimensions all have a minimum runnable impl; feedback loop is the deep focus — §A.4-D.
- TDD mandatory: red → green → refactor. No implementation before its failing test.
- One capability per task; each task ends with a commit. Commit messages note which agent did the work.
- Credentials: never hardcode/commit/log keys; `.env` is gitignored; view never echoes plaintext.
- CI: `.gitlab-ci.yml` with a `unit-test` job (and `image-build`); last pipeline must pass.

---

## File Structure

```
sumsch/
├── pyproject.toml              # package + pytest/ruff/mypy config
├── Makefile                    # make test / run / lint
├── src/harness/
│   ├── __init__.py
│   ├── actions.py              # Action dataclasses + Message + ParseError
│   ├── config.py               # load declarative config
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py             # LLMInterface, LLMResponse
│   │   ├── mock.py             # MockLLM (scripted)
│   │   └── deepseek.py         # DeepSeekClient (OpenAI-compatible)
│   ├── parser.py               # parse(raw) -> Action | ParseError
│   ├── guardrail.py            # guardrail() + Decision + HITL state
│   ├── dispatcher.py           # dispatch(action, ctx) -> ActionResult
│   ├── memory.py               # load_conventions(project) -> str
│   ├── context.py              # build_context(state) -> list[Message]
│   ├── loop.py                 # run(task, llm, config) -> Outcome
│   ├── feedback/
│   │   ├── __init__.py
│   │   ├── runner.py           # run_tests(target) -> TestResult
│   │   ├── parse.py            # parse_failures(TestResult) -> list[Failure]
│   │   ├── classifier.py       # classify(Failure) -> (FailureType, hint)
│   │   ├── composer.py         # compose(failures, state) -> Feedback
│   │   ├── selfcorrect.py      # update_state(state, failures) -> Status
│   │   └── pipeline.py         # pipeline(test_result, state) -> Feedback
│   └── auth/
│       ├── __init__.py
│       ├── store.py            # credential storage (keyring)
│       └── cli.py              # auth set/status/update/clear
├── arena/                      # kata content (test fixtures, not graded code)
│   ├── kata_assertion/  kata_import/  kata_syntax/
│   ├── kata_type/       kata_logic/    kata_timeout/
├── web/
│   ├── __init__.py
│   ├── app.py                  # HTTP API
│   └── ws.py                   # WebSocket streaming
├── tests/
│   ├── conftest.py
│   ├── test_actions.py test_config.py test_llm_mock.py test_parser.py
│   ├── test_guardrail.py test_dispatcher.py test_memory.py
│   ├── test_context.py test_loop.py
│   ├── feedback/test_runner.py test_parse.py test_classifier.py
│   ├── feedback/test_composer.py test_selfcorrect.py test_pipeline.py
│   ├── auth/test_store.py
│   └── demo/test_mechanism_demo.py   # §A.6 ①②③
├── Dockerfile  .gitlab-ci.yml  README.md
├── SPEC.md  PLAN.md  SPEC_PROCESS.md  AGENT_LOG.md  REFLECTION.md
└── render.yaml  (deploy)
```

**Dependency order / parallelism:** **Task 0 (scaffolding/import-path) is the prerequisite for ALL tasks — do it first.** After Task 0, T1–T3 (types, config, llm-mock) are independent → parallelizable. T4–T8 (parser/guardrail/dispatcher/memory/context) depend only on T1–T3 → parallelizable among themselves. T9 (arena) independent. T10–T15 (feedback) depend on T1+T9; T10–T14 parallelizable, T15 after them. T16 (loop) after T4–T8+T15. T17 (deepseek) after T3. T18 (auth) independent. T19 (demo) after T16. T20–T21 (web) after T16. T22–T26 (infra) late, parallelizable.

---

### Task 0: Project scaffolding (import path)

**Files:**
- Create: `pyproject.toml`, `src/harness/__init__.py`, `tests/conftest.py`, `tests/test_sanity.py`

**Interfaces:**
- Produces: importable `harness` package + pytest `pythonpath`. **Prerequisite for T1–T26.** (T22 later expands `pyproject.toml` with deps/ruff/mypy + adds Makefile; `tests/conftest.py` already exists here.)

- [ ] **Step 1: Write failing test**

```python
# tests/test_sanity.py
def test_harness_importable():
    import harness
    assert harness is not None
```

- [ ] **Step 2: Run test (fail)**

Run: `python -m pytest tests/test_sanity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness'`

- [ ] **Step 3: Implement**

```python
# src/harness/__init__.py
```

```toml
# pyproject.toml
[project]
name = "coding-agent-harness"
version = "0.1.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["tests"]
```

```python
# tests/conftest.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
```

- [ ] **Step 3b: Install pytest**

Run: `pip install pytest` (only pytest is needed for T0–T16; full dev deps `pip install -e ".[dev]"` come with T22's complete pyproject).

- [ ] **Step 4: Run test (pass)**

Run: `python -m pytest tests/test_sanity.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/harness/__init__.py tests/conftest.py tests/test_sanity.py
git commit -m "build: project scaffolding + import path (Task 0)"
```

---

### Task 1: Action & message types (`actions.py`)

**Files:**
- Create: `src/harness/actions.py`
- Test: `tests/test_actions.py`

**Interfaces:**
- Produces: `Message(role, content, tool_calls=None)`, `ParseError(msg)`, and actions `ReadFile(path)`, `EditFile(path, old, new)`, `RunShell(cmd)`, `RunTests(target)`, `Finish()` as frozen dataclasses; helper `is_action(obj)`.

- [ ] **Step 1: Write failing test**

```python
# tests/test_actions.py
from harness.actions import ReadFile, EditFile, RunShell, RunTests, Finish, Message, ParseError

def test_actions_carry_fields():
    assert ReadFile("a.py").path == "a.py"
    assert EditFile("a.py", "old", "new").new == "new"
    assert RunShell("ls").cmd == "ls"
    assert RunTests("tests/").target == "tests/"
    assert Finish() == Finish()

def test_message_and_parseerror():
    assert Message("user", "hi").role == "user"
    assert ParseError("bad").msg == "bad"
```

- [ ] **Step 2: Run test (fail)** — `pytest tests/test_actions.py -v` → FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

```python
# src/harness/actions.py
from dataclasses import dataclass
from typing import Literal, Optional

@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[list] = None

@dataclass(frozen=True)
class ParseError:
    msg: str

@dataclass(frozen=True)
class ReadFile:
    path: str

@dataclass(frozen=True)
class EditFile:
    path: str
    old: str
    new: str

@dataclass(frozen=True)
class RunShell:
    cmd: str

@dataclass(frozen=True)
class RunTests:
    target: str

@dataclass(frozen=True)
class Finish:
    pass

Action = object  # union hint for consumers
def is_action(obj) -> bool:
    return isinstance(obj, (ReadFile, EditFile, RunShell, RunTests, Finish))
```

- [ ] **Step 4: Run test (pass)** — `pytest tests/test_actions.py -v` → PASS.
- [ ] **Step 5: Commit** — `git add src/harness/actions.py tests/test_actions.py && git commit -m "feat(actions): typed action & message dataclasses"`

---

### Task 2: Config loader (`config.py`)

**Files:** Create `src/harness/config.py`; Test `tests/test_config.py`
**Interfaces:** Produces `Config(sandbox_root, retry_budget, denylist, warnlist, model, base_url, signals)` and `load_config(data: dict) -> Config`.

- [ ] **Step 1: Failing test**

```python
# tests/test_config.py
from harness.config import load_config

def test_load_config_defaults_and_overrides():
    cfg = load_config({"sandbox_root": "/tmp/arena", "retry_budget": 3})
    assert cfg.sandbox_root == "/tmp/arena"
    assert cfg.retry_budget == 3
    assert "rm -rf" in cfg.denylist
    assert cfg.model == "deepseek-chat"
```

- [ ] **Step 2: Run (fail)** — `pytest tests/test_config.py -v` → FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/config.py
from dataclasses import dataclass, field

DEFAULT_DENYLIST = ["rm -rf", "sudo", "drop ", "curl|sh", "wget|sh", ":(){:|:&};:"]

@dataclass
class Config:
    sandbox_root: str
    retry_budget: int = 5
    denylist: list = field(default_factory=lambda: list(DEFAULT_DENYLIST))
    warnlist: list = field(default_factory=list)
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com/v1"
    signals: list = field(default_factory=lambda: ["pytest"])

def load_config(data: dict) -> Config:
    return Config(
        sandbox_root=data["sandbox_root"],
        retry_budget=data.get("retry_budget", 5),
        denylist=data.get("denylist", list(DEFAULT_DENYLIST)),
        warnlist=data.get("warnlist", []),
        model=data.get("model", "deepseek-chat"),
        base_url=data.get("base_url", "https://api.deepseek.com/v1"),
        signals=data.get("signals", ["pytest"]),
    )
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(config): declarative config loader"`.

---

### Task 3: LLM abstraction + Mock (`llm/base.py`, `llm/mock.py`)

**Files:** Create `src/harness/llm/base.py`, `src/harness/llm/mock.py`, `src/harness/llm/__init__.py`; Test `tests/test_llm_mock.py`
**Interfaces:** Produces `LLMResponse(raw, content, tool_calls=None)`, `LLMInterface.complete(messages, tools=None) -> LLMResponse`, `MockLLM(script: list[str])`.

- [ ] **Step 1: Failing test**

```python
# tests/test_llm_mock.py
from harness.llm.mock import MockLLM
from harness.llm.base import LLMResponse

def test_mock_returns_scripted_then_finish():
    llm = MockLLM(script=['EDIT a.py old->new', 'FINISH'])
    r1 = llm.complete(messages=[])
    assert r1.content == 'EDIT a.py old->new'
    r2 = llm.complete(messages=[])
    assert r2.content == 'FINISH'

def test_mock_raises_when_exhausted():
    import pytest
    llm = MockLLM(script=['only'])
    llm.complete([])
    with pytest.raises(StopIteration):
        llm.complete([])
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/llm/base.py
from dataclasses import dataclass, field
from typing import Optional
from harness.actions import Message

@dataclass
class LLMResponse:
    raw: str
    content: str
    tool_calls: Optional[list] = field(default=None)

class LLMInterface:
    def complete(self, messages: list, tools: Optional[list] = None) -> LLMResponse:
        raise NotImplementedError
```

```python
# src/harness/llm/mock.py
from harness.llm.base import LLMInterface, LLMResponse

class MockLLM(LLMInterface):
    def __init__(self, script: list[str]):
        self._script = list(script)
        self._i = 0
    def complete(self, messages, tools=None) -> LLMResponse:
        if self._i >= len(self._script):
            raise StopIteration("MockLLM script exhausted")
        content = self._script[self._i]
        self._i += 1
        return LLMResponse(raw=content, content=content)
```

```python
# src/harness/llm/__init__.py
from .base import LLMInterface, LLMResponse
from .mock import MockLLM
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(llm): injectable abstraction + MockLLM"`.

---

### Task 4: Action parser (`parser.py`)

**Files:** Create `src/harness/parser.py`; Test `tests/test_parser.py`
**Interfaces:** Consumes `actions.*`. Produces `parse(raw: str) -> Action | ParseError`. Wire format: `EDIT <path> <old>-><new>`, `READ <path>`, `SHELL <cmd>`, `TEST <target>`, `FINISH`.

- [ ] **Step 1: Failing test**

```python
# tests/test_parser.py
from harness.parser import parse
from harness.actions import EditFile, ReadFile, RunShell, RunTests, Finish, ParseError

def test_parse_edit():
    assert parse("EDIT a.py old->new") == EditFile("a.py", "old", "new")
def test_parse_read_shell_test_finish():
    assert parse("READ a.py") == ReadFile("a.py")
    assert parse("SHELL ls -la") == RunShell("ls -la")
    assert parse("TEST tests/") == RunTests("tests/")
    assert parse("FINISH") == Finish()
def test_parse_error():
    assert isinstance(parse("nonsense"), ParseError)
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/parser.py
from harness.actions import EditFile, ReadFile, RunShell, RunTests, Finish, ParseError

def parse(raw: str):
    s = raw.strip()
    if s == "FINISH":
        return Finish()
    if s.startswith("EDIT "):
        rest = s[5:]
        path, sep, body = rest.partition(" ")
        if sep != " " or "->" not in body:
            return ParseError(f"bad EDIT: {raw}")
        old, new = body.split("->", 1)
        return EditFile(path, old, new)
    if s.startswith("READ "):
        return ReadFile(s[5:].strip())
    if s.startswith("SHELL "):
        return RunShell(s[6:])
    if s.startswith("TEST "):
        return RunTests(s[5:].strip())
    return ParseError(f"unrecognized action: {raw}")
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(parser): parse LLM wire format to actions"`.

---

### Task 5: Guardrail + HITL (`guardrail.py`)

**Files:** Create `src/harness/guardrail.py`; Test `tests/test_guardrail.py`
**Interfaces:** Consumes `actions.*`, `config.Config`. Produces `Decision` (Allow/Deny/RequireApproval + reason), `guardrail(action, cfg) -> Decision`, `is_within_sandbox(path, root) -> bool`, `HitlState` machine (`submit/decide`).

- [ ] **Step 1: Failing test**

```python
# tests/test_guardrail.py
from harness.guardrail import guardrail, is_within_sandbox, HitlState, Decision
from harness.actions import EditFile, RunShell, ReadFile, RunTests, Finish
from harness.config import load_config

cfg = load_config({"sandbox_root": "/sandbox"})

def test_blocks_rm_rf():
    d = guardrail(RunShell("rm -rf /"), cfg)
    assert d.kind == "Deny" and "rm -rf" in d.reason

def test_blocks_escape_edit():
    d = guardrail(EditFile("/etc/passwd", "x", "y"), cfg)
    assert d.kind == "Deny"

def test_allows_in_sandbox():
    assert guardrail(EditFile("/sandbox/a.py", "x", "y"), cfg).kind == "Allow"
    assert guardrail(ReadFile("/sandbox/a.py"), cfg).kind == "Allow"
    assert guardrail(RunTests("tests/"), cfg).kind == "Allow"
    assert guardrail(Finish(), cfg).kind == "Allow"

def test_warnlist_requires_approval():
    cfg2 = load_config({"sandbox_root": "/sandbox", "warnlist": ["git push"]})
    assert guardrail(RunShell("git push"), cfg2).kind == "RequireApproval"

def test_hitl_state_machine():
    h = HitlState()
    h.submit(RunShell("git push"))
    assert h.pending is not None
    h.decide(False)
    assert h.pending is None and h.last == "Denied"
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/guardrail.py
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
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(guardrail): sandbox fence, denylist, HITL state"`.

---

### Task 6: Dispatcher (`dispatcher.py`)

**Files:** Create `src/harness/dispatcher.py`; Test `tests/test_dispatcher.py`
**Interfaces:** Consumes `actions.*`, `config.Config`. Produces `ActionResult(ok, out, err, changed_files, test_result=None)`, `dispatch(action, cfg) -> ActionResult`. `RunTests` delegates to `feedback.runner.run_tests` (imported lazily to avoid cycles); for this task stub it via a callable injected in tests.

- [ ] **Step 1: Failing test**

```python
# tests/test_dispatcher.py
import os, tempfile
from harness.dispatcher import dispatch
from harness.actions import ReadFile, EditFile, RunShell, RunTests, Finish
from harness.config import load_config

def make_cfg(tmp):
    return load_config({"sandbox_root": str(tmp)})

def test_read_edit_in_sandbox(tmp_path):
    f = tmp_path / "a.py"; f.write_text("old")
    cfg = make_cfg(tmp_path)
    r = dispatch(ReadFile("a.py"), cfg)
    assert r.ok and "old" in r.out
    r = dispatch(EditFile("a.py", "old", "new"), cfg)
    assert r.ok and "new" in f.read_text()

def test_runshell_echo(tmp_path):
    cfg = make_cfg(tmp_path)
    r = dispatch(RunShell("echo hello"), cfg)
    assert r.ok and "hello" in r.out

def test_runtests_uses_injected_runner(tmp_path):
    cfg = make_cfg(tmp_path)
    called = {}
    def fake_runner(target, cfg):
        called["t"] = target; return type("T",(),{"exit_code":0,"stdout":"ok","signals":{}})()
    r = dispatch(RunTests("tests/"), cfg, test_runner=fake_runner)
    assert r.ok and called["t"] == "tests/"
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/dispatcher.py
import os, subprocess
from dataclasses import dataclass, field
from harness.actions import ReadFile, EditFile, RunShell, RunTests, Finish
from harness.config import Config

@dataclass
class ActionResult:
    ok: bool
    out: str = ""
    err: str = ""
    changed_files: list = field(default_factory=list)
    test_result: object = None

def _sandbox_path(path, root):
    return os.path.realpath(os.path.join(root, path)) if not os.path.isabs(path) else os.path.realpath(path)

def dispatch(action, cfg: Config, test_runner=None):
    if isinstance(action, ReadFile):
        p = _sandbox_path(action.path, cfg.sandbox_root)
        try:
            return ActionResult(ok=True, out=open(p, encoding="utf-8").read())
        except OSError as e:
            return ActionResult(ok=False, err=str(e))
    if isinstance(action, EditFile):
        p = _sandbox_path(action.path, cfg.sandbox_root)
        try:
            text = open(p, encoding="utf-8").read()
            text = text.replace(action.old, action.new)
            open(p, "w", encoding="utf-8").write(text)
            return ActionResult(ok=True, changed_files=[p])
        except OSError as e:
            return ActionResult(ok=False, err=str(e))
    if isinstance(action, RunShell):
        proc = subprocess.run(action.cmd, shell=True, cwd=cfg.sandbox_root,
                              capture_output=True, text=True, timeout=30)
        return ActionResult(ok=(proc.returncode == 0), out=proc.stdout, err=proc.stderr)
    if isinstance(action, RunTests):
        runner = test_runner
        if runner is None:
            from harness.feedback.runner import run_tests  # lazy
            runner = run_tests
        tr = runner(action.target, cfg)
        return ActionResult(ok=(tr.exit_code == 0), out=tr.stdout, test_result=tr)
    if isinstance(action, Finish):
        return ActionResult(ok=True, out="finished")
    return ActionResult(ok=False, err=f"unknown action {action}")
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(dispatcher): execute read/edit/shell/tests in sandbox"`.

---

### Task 7: Memory (`memory.py`)

**Files:** Create `src/harness/memory.py`; Test `tests/test_memory.py`
**Interfaces:** Produces `load_conventions(project_dir: str) -> str` (reads `CONVENTIONS.md` if present, else `""`).

- [ ] **Step 1: Failing test**

```python
# tests/test_memory.py
from harness.memory import load_conventions

def test_loads_conventions(tmp_path):
    (tmp_path / "CONVENTIONS.md").write_text("use 4 spaces")
    assert load_conventions(str(tmp_path)) == "use 4 spaces"

def test_missing_returns_empty(tmp_path):
    assert load_conventions(str(tmp_path)) == ""
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/memory.py
import os

def load_conventions(project_dir: str) -> str:
    p = os.path.join(project_dir, "CONVENTIONS.md")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return ""
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(memory): load per-project conventions"`.

---

### Task 8: Context builder (`context.py`)

**Files:** Create `src/harness/context.py`; Test `tests/test_context.py`
**Interfaces:** Consumes `actions.Message`, `memory.load_conventions`. Produces `State(history, retry_budget, status, current_kata)`, `build_context(state, cfg) -> list[Message]`.

- [ ] **Step 1: Failing test**

```python
# tests/test_context.py
from harness.context import build_context, State
from harness.config import load_config

def test_context_has_system_task_history_feedback(tmp_path):
    cfg = load_config({"sandbox_root": str(tmp_path)})
    st = State(history=[("tool", "ran tests")], retry_budget=3, status="running", current_kata="k1")
    msgs = build_context(st, cfg)
    roles = [m.role for m in msgs]
    assert roles[0] == "system"
    assert any("k1" in m.content for m in msgs)
    assert any("ran tests" in m.content for m in msgs)
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/context.py
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

def build_context(state: State, cfg: Config) -> list:
    conv = load_conventions(cfg.sandbox_root)
    msgs = [Message("system", SYSTEM_PROMPT + ("\n\nConventions:\n" + conv if conv else ""))]
    msgs.append(Message("user", f"Repair failing tests in kata: {state.current_kata}"))
    for role, content in state.history:
        msgs.append(Message(role, content))
    if state.last_feedback:
        msgs.append(Message("tool", state.last_feedback))
    return msgs
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(context): build LLM message list from state"`.

---

### Task 9: Arena kata fixtures (`arena/`)

**Files:** Create `arena/kata_assertion/{lib.py,test_lib.py,CONVENTIONS.md}` and analogous for `kata_import`, `kata_syntax`, `kata_type`, `kata_logic`, `kata_timeout`. No tests of their own — they are test fixtures consumed by T10/T15/T16/T19.
**Interfaces:** Produces 6 kata dirs, each with a failing test + a buggy source to repair.

- [ ] **Step 1: Create kata_assertion**

```python
# arena/kata_assertion/lib.py
def add(a, b):
    return a - b   # bug
# arena/kata_assertion/test_lib.py
def test_add():
    assert add(2, 3) == 5
# arena/kata_assertion/CONVENTIONS.md
# kata_assertion: the add function returns the wrong arithmetic.
```

- [ ] **Step 2: Create kata_import** — `lib.py` imports a non-existent module; `test_lib.py` imports lib.
- [ ] **Step 3: Create kata_syntax** — `lib.py` has a syntax error (unclosed paren); `test_lib.py` imports lib.
- [ ] **Step 4: Create kata_type** — `lib.py` returns `"5"` (str) where int expected; `test_lib.py` asserts `add(2,3) == 5` and `isinstance(add(2,3), int)`.
- [ ] **Step 5: Create kata_logic** — `lib.py` `is_even(n)` returns `n % 2 == 1` (inverted); `test_lib.py` asserts `is_even(4)`.
- [ ] **Step 6: Create kata_timeout** — `lib.py` `slow()` loops forever; `test_lib.py` asserts `slow() == 1` (runner enforces timeout).
- [ ] **Step 7: Verify each fails** — for each kata: `cd arena/<kata> && python -m pytest -q` → non-zero exit.
- [ ] **Step 8: Commit** — `git add arena && git commit -m "test(arena): 6 failing-test kata fixtures"`.

---

### Task 10: Feedback runner (`feedback/runner.py`)

**Files:** Create `src/harness/feedback/runner.py`, `src/harness/feedback/__init__.py`; Test `tests/feedback/test_runner.py`
**Interfaces:** Consumes `config.Config`. Produces `TestResult(exit_code, stdout, signals)`, `run_tests(target, cfg, timeout=30) -> TestResult`. Runs `python -m pytest <target>` with `cwd=sandbox_root`.

- [ ] **Step 1: Failing test**

```python
# tests/feedback/test_runner.py
import os, shutil, pathlib
from harness.feedback.runner import run_tests
from harness.config import load_config

def test_runner_reports_failure_for_buggy_kata(tmp_path):
    # copy kata_assertion fixture into sandbox
    src = pathlib.Path("arena/kata_assertion")
    shutil.copytree(src, tmp_path / "kata_assertion")
    cfg = load_config({"sandbox_root": str(tmp_path)})
    tr = run_tests("kata_assertion", cfg)
    assert tr.exit_code != 0
    assert "assert" in tr.stdout.lower() or "failed" in tr.stdout.lower()
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/feedback/runner.py
import subprocess
from dataclasses import dataclass, field
from harness.config import Config

@dataclass
class TestResult:
    exit_code: int
    stdout: str
    signals: dict = field(default_factory=dict)

def run_tests(target: str, cfg: Config, timeout: int = 30) -> TestResult:
    proc = subprocess.run(
        ["python", "-m", "pytest", "-q", "--no-header", target],
        cwd=cfg.sandbox_root, capture_output=True, text=True, timeout=timeout,
    )
    return TestResult(exit_code=proc.returncode, stdout=proc.stdout + proc.stderr,
                      signals={"pytest": proc.returncode})
```

```python
# src/harness/feedback/__init__.py
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(feedback/runner): run pytest in sandbox"`.

---

### Task 11: Failure parser (`feedback/parse.py`)

**Files:** Create `src/harness/feedback/parse.py`; Test `tests/feedback/test_parse.py`
**Interfaces:** Consumes `runner.TestResult`. Produces `Failure(file, line, assertion, expected, actual, traceback, type=None, hint=None)`, `parse_failures(test_result) -> list[Failure]`.

- [ ] **Step 1: Failing test**

```python
# tests/feedback/test_parse.py
from harness.feedback.parse import parse_failures, Failure
from harness.feedback.runner import TestResult

SAMPLE = """FAILED kata_assertion/test_lib.py::test_add - assert (2-3) == 5
assert (2-3) == 5
 where (2-3) = -1
kata_assertion/lib.py:2: AssertionError"""

def test_parse_extracts_failure():
    fs = parse_failures(TestResult(1, SAMPLE))
    assert len(fs) == 1
    assert fs[0].file == "kata_assertion/test_lib.py"
    assert "assert" in fs[0].assertion

def test_parse_empty_when_passing():
    assert parse_failures(TestResult(0, "1 passed")) == []
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/feedback/parse.py
import re
from dataclasses import dataclass
from harness.feedback.runner import TestResult

@dataclass
class Failure:
    file: str
    line: int = None
    assertion: str = None
    expected: str = None
    actual: str = None
    traceback: str = ""
    type: str = None
    hint: str = None

_FAIL_RE = re.compile(r"FAILED\s+(\S+?)::(\S+?)\s+-\s+(.*)")
_LINE_RE = re.compile(r"(.+?):(\d+):\s*(AssertionError|Error)?")

def parse_failures(tr: TestResult) -> list:
    failures = []
    for m in _FAIL_RE.finditer(tr.stdout):
        file, _test, assertion = m.group(1), m.group(2), m.group(3)
        line = None
        lm = re.search(re.escape(file) + r":(\d+):", tr.stdout)
        if lm:
            line = int(lm.group(1))
        failures.append(Failure(file=file, line=line, assertion=assertion, traceback=m.group(0)))
    if tr.exit_code == 0:
        return []
    return failures or [Failure(file="<unknown>", traceback=tr.stdout)]
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(feedback/parse): parse pytest output to failures"`.

---

### Task 12: Failure classifier (`feedback/classifier.py`)

**Files:** Create `src/harness/feedback/classifier.py`; Test `tests/feedback/test_classifier.py`
**Interfaces:** Consumes `parse.Failure`. Produces `FailureType` (enum: assertion/import/syntax/type/logic/timeout), `classify(failure) -> tuple[str, str]` (type, hint).

- [ ] **Step 1: Failing test**

```python
# tests/feedback/test_classifier.py
from harness.feedback.classifier import classify
from harness.feedback.parse import Failure

def test_classify_assertion():
    t, h = classify(Failure(file="x", assertion="assert 4==5", traceback="AssertionError"))
    assert t == "assertion"
def test_classify_import():
    t, _ = classify(Failure(file="x", traceback="ModuleNotFoundError: No module named 'x'"))
    assert t == "import"
def test_classify_syntax():
    t, _ = classify(Failure(file="x", traceback="SyntaxError: unexpected EOF"))
    assert t == "syntax"
def test_classify_type():
    t, _ = classify(Failure(file="x", traceback="TypeError: unsupported operand"))
    assert t == "type"
def test_classify_timeout():
    t, _ = classify(Failure(file="x", traceback="TimeoutExpired"))
    assert t == "timeout"
def test_classify_logic_default():
    t, _ = classify(Failure(file="x", assertion="assert is_even(4)", traceback="AssertionError"))
    assert t == "logic"
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/feedback/classifier.py
from harness.feedback.parse import Failure

TYPES = ["assertion", "import", "syntax", "type", "logic", "timeout"]
HINTS = {
    "assertion": "Check the failing assertion's expected vs actual; the implementation likely returns a wrong value.",
    "import": "A module import failed; fix the import path or create the missing module.",
    "syntax": "A syntax error; fix the malformed statement in the flagged file.",
    "type": "A type error; ensure operands/return types match what the test expects.",
    "logic": "Logic error; the function runs but returns an incorrect result. Re-read the test intent.",
    "timeout": "The test timed out; eliminate infinite loops or slow paths.",
}

def classify(f: Failure) -> tuple:
    tb = (f.traceback or "")
    if "TimeoutExpired" in tb:
        return "timeout", HINTS["timeout"]
    if "ModuleNotFoundError" in tb or "ImportError" in tb:
        return "import", HINTS["import"]
    if "SyntaxError" in tb:
        return "syntax", HINTS["syntax"]
    if "TypeError" in tb:
        return "type", HINTS["type"]
    if f.assertion and "AssertionError" in tb:
        # distinguish pure value-mismatch (logic) from explicit assert
        if "==" in f.assertion or "is " in f.assertion:
            return "logic", HINTS["logic"]
        return "assertion", HINTS["assertion"]
    return "logic", HINTS["logic"]
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(feedback/classifier): rule-based failure taxonomy"`.

---

### Task 13: Feedback composer (`feedback/composer.py`)

**Files:** Create `src/harness/feedback/composer.py`; Test `tests/feedback/test_composer.py`
**Interfaces:** Consumes `parse.Failure`, `classifier.classify`, `context.State`. Produces `Feedback(text, failures, retry_state)`, `compose(failures, state) -> Feedback`.

- [ ] **Step 1: Failing test**

```python
# tests/feedback/test_composer.py
from harness.feedback.composer import compose, Feedback
from harness.feedback.parse import Failure
from harness.context import State

def test_compose_includes_failure_and_hint():
    fs = [Failure(file="a.py", line=2, assertion="assert 4==5", traceback="AssertionError")]
    fb = compose(fs, State(retry_budget=3, current_kata="k1"))
    assert isinstance(fb, Feedback)
    assert "a.py" in fb.text and "budget" in fb.text.lower()
    assert fb.failures and fb.retry_state["budget"] == 3
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/feedback/composer.py
from dataclasses import dataclass, field
from harness.feedback.parse import Failure
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
        f.type = ftype; f.hint = hint
        lines.append(f"- {f.file}:{f.line or '?'} [{ftype}] {f.assertion or ''}\n  hint: {hint}")
    if not failures:
        lines.append("All tests passed.")
    return Feedback(text="\n".join(lines), failures=failures,
                    retry_state={"budget": state.retry_budget, "status": state.status})
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(feedback/composer): compose structured feedback"`.

---

### Task 14: Self-correction strategy (`feedback/selfcorrect.py`)

**Files:** Create `src/harness/feedback/selfcorrect.py`; Test `tests/feedback/test_selfcorrect.py`
**Interfaces:** Consumes `context.State`, `parse.Failure`. Produces `update_state(state, failures) -> str` (status: running/done/aborted), `STATUS_*` constants. Rules: no failures → done; budget hits 0 → aborted; same failure-type repeated ≥3 → escalate (status running but mark escalation); else running.

- [ ] **Step 1: Failing test**

```python
# tests/feedback/test_selfcorrect.py
from harness.feedback.selfcorrect import update_state
from harness.context import State
from harness.feedback.parse import Failure

def test_no_failures_done():
    assert update_state(State(retry_budget=2), []) == "done"
def test_budget_zero_aborted():
    s = State(retry_budget=0)
    assert update_state(s, [Failure(file="a", traceback="AssertionError")]) == "aborted"
def test_escalation_after_repeats():
    s = State(retry_budget=4, current_kata="k")
    for _ in range(3):
        st = update_state(s, [Failure(file="a", traceback="AssertionError", assertion="x==y")])
    assert st == "running"
    assert s.escalated is True
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/feedback/selfcorrect.py
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
```

(Add `escalated: bool = False` and `_repeat_counts` as dynamic attrs to `State` in `context.py` — or add fields. Update `context.State` dataclass: add `escalated: bool = False`.)

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(feedback/selfcorrect): retry budget, escalation, termination"`.

---

### Task 15: Feedback pipeline wiring (`feedback/pipeline.py`)

**Files:** Create `src/harness/feedback/pipeline.py`; Test `tests/feedback/test_pipeline.py`
**Interfaces:** Consumes T10–T14. Produces `pipeline(test_result, state) -> Feedback` (run→parse→classify→compose + selfcorrect). Also sets `state.last_feedback`.

- [ ] **Step 1: Failing test**

```python
# tests/feedback/test_pipeline.py
from harness.feedback.pipeline import pipeline
from harness.feedback.runner import TestResult
from harness.context import State

def test_pipeline_classifies_and_updates_state():
    tr = TestResult(1, "FAILED a/test_x.py::test_t - assert 4==5\na/lib.py:2: AssertionError")
    s = State(retry_budget=3, current_kata="a")
    fb = pipeline(tr, s)
    assert "a/test_x.py" in fb.text
    assert s.retry_budget == 2          # decremented
    assert s.status == "running"
def test_pipeline_done_on_pass():
    s = State(retry_budget=3)
    fb = pipeline(TestResult(0, "1 passed"), s)
    assert s.status == "done" and "passed" in fb.text.lower()
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/feedback/pipeline.py
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
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(feedback/pipeline): wire run->parse->classify->compose->selfcorrect"`.

---

### Task 16: Main loop (`loop.py`) + §A.6 demos ②③

**Files:** Create `src/harness/loop.py`; Test `tests/test_loop.py`
**Interfaces:** Consumes all. Produces `Outcome(status, turns, final_test_result)`, `run(task, llm, cfg) -> Outcome`. Each turn: build_context → llm.complete → parse → guardrail (HITL auto-deny in mock tests) → dispatch → if RunTests, pipeline → append to history → stop_check.

- [ ] **Step 1: Failing test (demos ② self-correct, ③ budget-exhaust abort)**

```python
# tests/test_loop.py
import shutil, pathlib
from harness.loop import run
from harness.llm.mock import MockLLM
from harness.config import load_config

def _seed_arena(tmp):
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp / "kata_assertion")

def test_loop_self_corrects_to_green(tmp_path):
    _seed_arena(tmp_path)
    cfg = load_config({"sandbox_root": str(tmp_path), "retry_budget": 3})
    # turn1: wrong fix (multiply), turn2: correct fix (add), turn3: test, turn4: finish
    llm = MockLLM(script=[
        "EDIT kata_assertion/lib.py return a - b->return a * b",
        "EDIT kata_assertion/lib.py return a * b->return a + b",
        "TEST kata_assertion",
        "FINISH",
    ])
    out = run("kata_assertion", llm, cfg)
    assert out.status == "done"
    assert out.final_test_result.exit_code == 0

def test_loop_aborts_on_budget_exhaustion(tmp_path):
    _seed_arena(tmp_path)
    cfg = load_config({"sandbox_root": str(tmp_path), "retry_budget": 1})
    llm = MockLLM(script=["EDIT kata_assertion/lib.py return a - b->return a * b", "TEST kata_assertion"])
    out = run("kata_assertion", llm, cfg)
    assert out.status == "aborted"
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/loop.py
from dataclasses import dataclass
from harness.context import build_context, State
from harness.parser import parse
from harness.guardrail import guardrail
from harness.dispatcher import dispatch
from harness.feedback.pipeline import pipeline
from harness.config import Config

@dataclass
class Outcome:
    status: str
    turns: int
    final_test_result: object = None

def run(task: str, llm, cfg: Config, max_turns: int = 20) -> Outcome:
    state = State(retry_budget=cfg.retry_budget, current_kata=task)
    final = None
    for turn in range(max_turns):
        msgs = build_context(state, cfg)
        resp = llm.complete(messages=msgs)
        action = parse(resp.content)
        from harness.actions import ParseError, RunTests, Finish
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
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(loop): main loop with feedback self-correction (§A.6 ②③)"`.

---

### Task 17: DeepSeek LLM client (`llm/deepseek.py`)

**Files:** Create `src/harness/llm/deepseek.py`; Test `tests/test_llm_deepseek.py` (offline: mock httpx).
**Interfaces:** Consumes `llm.base.LLMInterface`, `auth.store.get_key`. Produces `DeepSeekClient(model, base_url)`; `complete()` calls `/chat/completions` via httpx using key from store; never logs key.

- [ ] **Step 1: Failing test (httpx mocked)**

```python
# tests/test_llm_deepseek.py
from harness.llm.deepseek import DeepSeekClient

def test_complete_calls_api(monkeypatch):
    calls = {}
    def fake_post(url, *, headers=None, json=None, timeout=None):
        calls["url"] = url; calls["auth"] = headers.get("Authorization")
        class R:
            status_code = 200
            def raise_for_status(self): pass
            def json(self): return {"choices":[{"message":{"content":"EDIT a.py x->y"}}]}
        return R()
    monkeypatch.setattr("harness.llm.deepseek.httpx.post", fake_post)
    monkeypatch.setattr("harness.auth.store.get_key", lambda: "sk-test")
    c = DeepSeekClient(model="deepseek-chat", base_url="https://api.deepseek.com/v1")
    r = c.complete(messages=[{"role":"user","content":"fix"}])
    assert r.content == "EDIT a.py x->y"
    assert calls["auth"] == "Bearer sk-test"
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/llm/deepseek.py
import httpx
from harness.llm.base import LLMInterface, LLMResponse
from harness.auth.store import get_key

class DeepSeekClient(LLMInterface):
    def __init__(self, model="deepseek-chat", base_url="https://api.deepseek.com/v1"):
        self.model = model
        self.base_url = base_url
    def complete(self, messages, tools=None) -> LLMResponse:
        key = get_key()
        if not key:
            raise RuntimeError("DeepSeek key not set; run: harness auth set")
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        return LLMResponse(raw=str(data), content=content)
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(llm/deepseek): OpenAI-compatible client, key from store"`.

---

### Task 18: Credential storage + CLI (`auth/store.py`, `auth/cli.py`)

**Files:** Create `src/harness/auth/store.py`, `src/harness/auth/cli.py`, `src/harness/auth/__init__.py`; Test `tests/auth/test_store.py`
**Interfaces:** Produces `get_key() -> str|None`, `set_key(value)`, `clear_key()`, `has_key() -> bool` (via `keyring` — service `harness.deepseek`, account `default`); CLI `auth set/status/update/clear` with hidden input & no-echo status.

- [ ] **Step 1: Failing test (fake keyring backend)**

```python
# tests/auth/test_store.py
import keyring, pytest
from harness.auth import store

@pytest.fixture(autouse=True)
def fake_keyring(monkeypatch):
    mem = {}
    monkeypatch.setattr(keyring, "set_password", lambda s, a, v: mem.__setitem__((s,a), v))
    monkeypatch.setattr(keyring, "get_password", lambda s, a: mem.get((s,a)))
    monkeypatch.setattr(keyring, "delete_password", lambda s, a: mem.pop((s,a), None))
    return mem

def test_set_get_clear_no_echo():
    assert store.get_key() is None
    store.set_key("sk-secret")
    assert store.has_key() is True
    assert store.get_key() == "sk-secret"
    store.clear_key()
    assert store.has_key() is False
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# src/harness/auth/store.py
import keyring

SERVICE = "harness.deepseek"
ACCOUNT = "default"

def get_key() -> str | None:
    return keyring.get_password(SERVICE, ACCOUNT)

def has_key() -> bool:
    return get_key() is not None

def set_key(value: str):
    keyring.set_password(SERVICE, ACCOUNT, value)

def clear_key():
    try:
        keyring.delete_password(SERVICE, ACCOUNT)
    except keyring.errors.PasswordDeleteError:
        pass
```

```python
# src/harness/auth/cli.py
import getpass
from harness.auth import store

def status():
    print("DeepSeek key: " + ("set" if store.has_key() else "NOT set"))  # never echo value

def set_():
    v = getpass.getpass("DeepSeek API key (hidden): ")
    if v:
        store.set_key(v); print("stored.")

def update():
    set_()

def clear():
    store.clear_key(); print("cleared.")
```

```python
# src/harness/auth/__init__.py
from . import store
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(auth): keyring credential store + no-echo CLI"`.

---

### Task 19: §A.6 mechanism demo (`tests/demo/test_mechanism_demo.py`)

**Files:** Create `tests/demo/test_mechanism_demo.py`; (depends on T5, T16). Demonstrates ① guardrail intercept, ② feedback self-correction, ③ classifier+budget abort — all under MockLLM, deterministic.

- [ ] **Step 1: Write the demo test**

```python
# tests/demo/test_mechanism_demo.py
import shutil, pathlib
from harness.guardrail import guardrail
from harness.actions import RunShell, EditFile
from harness.config import load_config
from harness.loop import run
from harness.llm.mock import MockLLM

cfg = load_config({"sandbox_root": "/sandbox"})

def test_demo1_guardrail_intercepts_dangerous_action():
    assert guardrail(RunShell("rm -rf /"), cfg).kind == "Deny"
    assert guardrail(EditFile("/etc/passwd", "x", "y"), cfg).kind == "Deny"

def test_demo2_feedback_drives_self_correction(tmp_path):
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp_path / "kata_assertion")
    c = load_config({"sandbox_root": str(tmp_path), "retry_budget": 3})
    llm = MockLLM(script=[
        "EDIT kata_assertion/lib.py return a - b->return a * b",
        "EDIT kata_assertion/lib.py return a * b->return a + b",
        "TEST kata_assertion", "FINISH",
    ])
    out = run("kata_assertion", llm, c)
    assert out.status == "done" and out.final_test_result.exit_code == 0

def test_demo3_classifier_and_budget_abort(tmp_path):
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp_path / "kata_assertion")
    c = load_config({"sandbox_root": str(tmp_path), "retry_budget": 1})
    llm = MockLLM(script=["EDIT kata_assertion/lib.py return a - b->return a * b", "TEST kata_assertion"])
    out = run("kata_assertion", llm, c)
    assert out.status == "aborted"
```

- [ ] **Step 2: Run** — `pytest tests/demo/test_mechanism_demo.py -v` → PASS (deterministic, no network).
- [ ] **Step 3: Commit** — `git commit -m "test(demo): §A.6 mechanism demo ①②③ under MockLLM"`.

---

### Task 20: WebUI HTTP API (`web/app.py`)

**Files:** Create `web/app.py`, `web/__init__.py`; Test `tests/test_web_app.py` (FastAPI TestClient).
**Interfaces:** Consumes `loop.run`, `llm.mock.MockLLM`. Produces `app` (FastAPI) with `POST /tasks` → `{"status","turns"}` using MockLLM in tests.

- [ ] **Step 1: Failing test**

```python
# tests/test_web_app.py
import shutil, pathlib
from fastapi.testclient import TestClient
from web.app import app, set_runtime

def test_post_task_runs_loop(tmp_path):
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp_path / "kata_assertion")
    from harness.config import load_config
    from harness.llm.mock import MockLLM
    cfg = load_config({"sandbox_root": str(tmp_path), "retry_budget": 3})
    llm = MockLLM(script=["EDIT kata_assertion/lib.py return a - b->return a + b","TEST kata_assertion","FINISH"])
    set_runtime(llm=llm, cfg=cfg)
    c = TestClient(app)
    r = c.post("/tasks", json={"kata": "kata_assertion"})
    assert r.status_code == 200 and r.json()["status"] == "done"
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement**

```python
# web/app.py
from fastapi import FastAPI
from pydantic import BaseModel
from harness.loop import run

app = FastAPI()
_runtime = {}

class TaskReq(BaseModel):
    kata: str

def set_runtime(*, llm, cfg):
    _runtime["llm"] = llm
    _runtime["cfg"] = cfg

@app.post("/tasks")
def post_tasks(req: TaskReq):
    out = run(req.kata, _runtime["llm"], _runtime["cfg"])
    return {"status": out.status, "turns": out.turns}
```

```python
# web/__init__.py
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(web): HTTP API over loop"`.

---

### Task 21: WebUI WebSocket streaming (`web/ws.py`)

**Files:** Create `web/ws.py`; Modify `web/app.py` to mount WS; Test `tests/test_web_ws.py`.
**Interfaces:** Consumes `loop.run` (refactor loop to accept an `on_event` callback emitting per-turn dicts). Produces `WS /stream` yielding `{"turn","action","result","feedback"}`.

- [ ] **Step 1: Failing test**

```python
# tests/test_web_ws.py
import shutil, pathlib, json
from fastapi.testclient import TestClient
from web.app import app, set_runtime
from harness.config import load_config
from harness.llm.mock import MockLLM

def test_stream_emits_turn_events(tmp_path):
    shutil.copytree(pathlib.Path("arena/kata_assertion"), tmp_path / "kata_assertion")
    cfg = load_config({"sandbox_root": str(tmp_path), "retry_budget": 3})
    llm = MockLLM(script=["EDIT kata_assertion/lib.py return a - b->return a + b","TEST kata_assertion","FINISH"])
    set_runtime(llm=llm, cfg=cfg)
    c = TestClient(app)
    with c.websocket_connect("/stream?kata=kata_assertion") as ws:
        events = []
        while True:
            try:
                events.append(json.loads(ws.receive_text()))
            except Exception:
                break
    assert any("action" in e for e in events)
```

- [ ] **Step 2: Run (fail)** — FAIL.
- [ ] **Step 3: Implement** — refactor `loop.run` to accept `on_event=None`:

```python
# in loop.run signature: def run(task, llm, cfg, max_turns=20, on_event=None)
# after dispatch each turn:
#   if on_event: on_event({"turn": turn, "action": repr(action), "result": result.out or result.err, "feedback": state.last_feedback})
```

```python
# web/ws.py
from fastapi import WebSocket
from harness.loop import run

async def stream(ws: WebSocket, kata: str, llm, cfg):
    await ws.accept()
    def on_event(e):
        import json
        ws.send_text(json.dumps(e))
    out = run(kata, llm, cfg, on_event=on_event)
    ws.send_text(json.dumps({"status": out.status, "turns": out.turns}))
```

Add to `web/app.py`:
```python
from web.ws import stream as ws_stream
from fastapi import WebSocket
@app.websocket("/stream")
async def stream_endpoint(ws: WebSocket):
    kata = ws.query_params.get("kata", "")
    await ws_stream(ws, kata, _runtime["llm"], _runtime["cfg"])
```

- [ ] **Step 4: Run (pass)** — PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(web): WebSocket streaming of loop turns"`.

---

### Task 22: Project packaging (`pyproject.toml`, `Makefile`, `conftest.py`)

**Files:** Modify `pyproject.toml` (expand from Task 0), Create `Makefile`. (`tests/conftest.py` already created in Task 0 — do not recreate.)
**Interfaces:** `make test` → `python -m pytest -q`; `make run` → `uvicorn web.app:app`; `make lint` → `ruff check . && mypy src`.

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "coding-agent-harness"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["httpx>=0.27", "keyring>=25", "fastapi>=0.110", "uvicorn>=0.29"]

[project.optional-dependencies]
dev = ["pytest>=8,<9", "ruff>=0.6", "mypy>=1.11", "httpx>=0.27"]

[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.mypy]
packages = ["harness"]
```

- [ ] **Step 2: Create Makefile**

```make
test:
	python -m pytest -q
run:
	uvicorn web.app:app --reload --port 8000
lint:
	ruff check . && mypy src
```

- [ ] **Step 3: Create tests/conftest.py**

```python
# tests/conftest.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
```

- [ ] **Step 4: Run** — `make test` → all green.
- [ ] **Step 5: Commit** — `git commit -m "build: pyproject, Makefile, conftest"`.

---

### Task 23: Dockerfile

**Files:** Create `Dockerfile`; (no test — validated in CI image-build).
**Interfaces:** Builds image with Python 3.11, installs deps, bundles src+arena+web, exposes 8000, runs uvicorn.

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir . && pip install --no-cache-dir uvicorn
COPY src ./src
COPY arena ./arena
COPY web ./web
COPY tests ./tests
ENV PYTHONPATH=/app/src:/app
EXPOSE 8000
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Build (manual/CI)** — `docker build -t harness .` → succeeds.
- [ ] **Step 3: Commit** — `git commit -m "build: Dockerfile"`.

---

### Task 24: CI (`.gitlab-ci.yml`)

**Files:** Create `.gitlab-ci.yml`.
**Interfaces:** `unit-test` job (pytest) + `image-build` job (docker build). Last pipeline must pass.

- [ ] **Step 1: Create .gitlab-ci.yml**

```yaml
image: python:3.11

stages:
  - test
  - build

unit-test:
  stage: test
  script:
    - pip install -e ".[dev]"
    - make test
  artifacts:
    reports:
      junit: test-results.xml

image-build:
  stage: build
  image: docker:24
  services: [docker:24-dind]
  script:
    - docker build -t harness:$CI_COMMIT_SHORT_SHA .
  only:
    - main
```

- [ ] **Step 2: Commit** — `git commit -m "ci: unit-test + image-build jobs"`.

---

### Task 25: README.md

**Files:** Create `README.md`.
**Interfaces:** Required sections: 简介/安装/运行/分发命令/目录结构/安全边界.

- [ ] **Step 1: Write README** (sections: Project intro, Install (`pip install -e ".[dev]"`), Run (`make run` / `docker run -p 8000:8000 harness`), Distribution commands, Directory structure, Security boundaries (credential threat model summary, sandbox fence, denylist), Known limitations).
- [ ] **Step 2: Commit** — `git commit -m "docs: README"`.

---

### Task 26: Deploy config (`render.yaml`)

**Files:** Create `render.yaml`; (user deploys with their account).
**Interfaces:** Web service running the Docker image, DeepSeek key via Render secret env.

- [ ] **Step 1: Create render.yaml**

```yaml
services:
  - type: web
    name: coding-agent-harness
    env: docker
    plan: free
    healthCheckPath: /docs
    envVars:
      - key: DEEPSEEK_API_KEY
        sync: false   # set via Render dashboard (secret)
```

- [ ] **Step 2: Commit** — `git commit -m "deploy: render.yaml"`.
- [ ] **Step 3 (user):** Push to NJU GitLab, connect repo on Render, set `DEEPSEEK_API_KEY` secret, deploy → public URL.

---

## Self-Review (run by plan author)

1. **Spec coverage:** §3.1 llm→T3,T17; §3.2 actions/parser→T1,T4; §3.3 dispatcher→T6; §3.4 guardrail+HITL→T5; §3.5 feedback pipeline→T10–T15; §3.6 context/memory→T7,T8; §3.7 loop→T16; §3.8 config→T2; §3.9 arena→T9; §3.10 web→T20,T21; §3.11 auth→T18; §A.6 demo→T19; §7 distro→T23,T24,T26; README→T25. All sections covered. ✓
2. **Placeholder scan:** No TBD/TODO; every step has code or a concrete file. ✓
3. **Type consistency:** `Failure` fields used identically in T11–T13; `State` fields (`retry_budget`,`status`,`current_kata`,`last_feedback`) consistent T8–T16; `run_tests(target, cfg)` signature consistent T6/T10; `Decision.kind` strings ("Allow"/"Deny"/"RequireApproval") consistent T5/T16; `MockLLM(script)` consistent T3/T16/T19/T20. ✓ (Note: T14 adds `escalated` to `State` — update `context.State` dataclass accordingly, flagged in T14.)

---

## Execution Handoff

Plan complete and saved to `PLAN.md`. Per homework §4.5, the **next step is cold-start verification with a different agent type** (fresh session, only SPEC.md + PLAN.md) — this must happen before executing any task. After cold-start passes, choose execution mode:

1. **Subagent-Driven (recommended)** — fresh subagent per task via superpowers:subagent-driven-development, two-stage review between tasks.
2. **Inline Execution** — execute tasks in-session via superpowers:executing-plans, batched with checkpoints.
