from harness.memory import compress_history


def test_compress_keeps_system_and_last_n():
    history = [
        ("user", "msg1"),
        ("user", "msg2"),
        ("user", "msg3"),
        ("user", "msg4"),
        ("user", "msg5"),
        ("user", "msg6"),
        ("user", "msg7"),
        ("user", "msg8"),
    ]
    compressed = compress_history(history, max_messages=4)
    # Should keep first (msg1 as context) + last 3
    assert len(compressed) == 4
    assert compressed[0][1] == "msg1"
    assert compressed[-1][1] == "msg8"


def test_compress_noop_when_under_limit():
    history = [("user", "a"), ("user", "b")]
    compressed = compress_history(history, max_messages=10)
    assert compressed == history


def test_compress_empty_history():
    assert compress_history([], max_messages=5) == []


def test_compress_inserts_truncation_notice():
    history = [("user", f"msg{i}") for i in range(50)]
    compressed = compress_history(history, max_messages=10)
    # First message kept, truncation notice, last 8 messages
    assert any("truncated" in c[1].lower() or "omitted" in c[1].lower() for c in compressed)
    assert compressed[0][1] == "msg0"
    assert compressed[-1][1] == "msg49"


def test_compress_exact_limit():
    history = [("user", "a"), ("user", "b"), ("user", "c")]
    compressed = compress_history(history, max_messages=3)
    assert compressed == history
