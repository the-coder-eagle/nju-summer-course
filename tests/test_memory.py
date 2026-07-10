from harness.memory import load_conventions


def test_loads_conventions(tmp_path):
    (tmp_path / "CONVENTIONS.md").write_text("use 4 spaces")
    assert load_conventions(str(tmp_path)) == "use 4 spaces"


def test_missing_returns_empty(tmp_path):
    assert load_conventions(str(tmp_path)) == ""
