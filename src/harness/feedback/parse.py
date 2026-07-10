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
