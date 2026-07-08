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
