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


_RUFF_RE = re.compile(r"^(\S+?):(\d+):(\d+):\s+(\S+)\s+(.+)", re.MULTILINE)


def parse_failures(tr: TestResult) -> list:
    failures = []

    # Parse pytest failures
    for m in _FAIL_RE.finditer(tr.stdout):
        file, _test, assertion = m.group(1), m.group(2), m.group(3)
        line = None
        lm = re.search(re.escape(file) + r":(\d+):", tr.stdout)
        if lm:
            line = int(lm.group(1))
        failures.append(Failure(file=file, line=line, assertion=assertion, traceback=m.group(0)))

    # Parse ruff lint issues (path:line:col: CODE message)
    for m in _RUFF_RE.finditer(tr.stdout):
        file, line_str, col, code, msg = m.groups()
        failures.append(Failure(
            file=file, line=int(line_str),
            assertion=f"{code}: {msg}",
            traceback=m.group(0),
            type="style",
        ))

    if tr.exit_code == 0:
        return []
    return failures or [Failure(file="<unknown>", traceback=tr.stdout)]
