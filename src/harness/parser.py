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
