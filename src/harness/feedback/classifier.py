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
