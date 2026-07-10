from harness.feedback.classifier import classify
from harness.feedback.parse import Failure


def test_classify_assertion():
    t, h = classify(Failure(file="x", assertion="assert False", traceback="AssertionError"))
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
    t, _ = classify(Failure(file="x", assertion="assert add(2,3) == 5", traceback="AssertionError"))
    assert t == "logic"
