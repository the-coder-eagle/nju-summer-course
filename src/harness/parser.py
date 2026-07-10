import re
from harness.actions import EditFile, ReadFile, RunShell, RunTests, Finish, ParseError


def parse(raw: str):
    """Parse the first valid action from the LLM response."""
    s = raw.strip()

    # EDIT: match multiline EDIT with -> separator (possibly on its own line)
    m = re.search(r'^EDIT\s+(\S+)\s+(.+?)\s*->\s*(.+)$', s, re.MULTILINE | re.DOTALL)
    if m:
        path = m.group(1)
        old = m.group(2)
        new = m.group(3)
        return EditFile(path, old, new)

    # Single-line actions
    for line in s.split("\n"):
        line = line.strip()
        if line == "FINISH":
            return Finish()
        if line.startswith("READ "):
            return ReadFile(line[5:].strip())
        if line.startswith("SHELL "):
            return RunShell(line[6:].strip())
        if line.startswith("TEST "):
            return RunTests(line[5:].strip())

    return ParseError(f"unrecognized action: {s[:100]}")
