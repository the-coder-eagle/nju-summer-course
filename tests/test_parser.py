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
