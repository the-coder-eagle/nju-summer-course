from harness.dispatcher import dispatch
from harness.actions import ReadFile, EditFile, RunShell, RunTests
from harness.config import load_config


def make_cfg(tmp):
    return load_config({"sandbox_root": str(tmp)})


def test_read_edit_in_sandbox(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("old")
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
        called["t"] = target
        return type("T", (), {"exit_code": 0, "stdout": "ok", "signals": {}})()

    r = dispatch(RunTests("tests/"), cfg, test_runner=fake_runner)
    assert r.ok and called["t"] == "tests/"
