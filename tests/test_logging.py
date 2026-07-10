import json
import os
from harness.logging import EventLogger, replay_log


def test_logger_writes_jsonl(tmp_path):
    logfile = tmp_path / "events.jsonl"
    logger = EventLogger(str(logfile))
    logger.log(turn=0, action="EDIT a.py x->y", result="ok", feedback="")
    logger.log(turn=1, action="TEST .", result="1 passed", feedback="done")
    logger.close()

    lines = logfile.read_text().strip().split("\n")
    assert len(lines) == 2
    e0 = json.loads(lines[0])
    assert e0["turn"] == 0 and e0["action"] == "EDIT a.py x->y"
    e1 = json.loads(lines[1])
    assert e1["turn"] == 1 and e1["result"] == "1 passed"


def test_replay_reads_log(tmp_path):
    logfile = tmp_path / "events.jsonl"
    logger = EventLogger(str(logfile))
    logger.log(turn=0, action="READ f.py", result="content", feedback="")
    logger.log(turn=1, action="FINISH", result="done", feedback="pass")
    logger.close()

    events = replay_log(str(logfile))
    assert len(events) == 2
    assert events[0]["action"] == "READ f.py"
    assert events[1]["action"] == "FINISH"


def test_replay_empty_log(tmp_path):
    logfile = tmp_path / "empty.jsonl"
    logfile.write_text("")
    assert replay_log(str(logfile)) == []


def test_replay_skips_malformed_lines(tmp_path):
    logfile = tmp_path / "bad.jsonl"
    logfile.write_text('{"turn":0}\nnot-json\n{"turn":1,"action":"ok"}\n')
    events = replay_log(str(logfile))
    assert len(events) == 2  # skips the bad line


def test_logger_file_not_found_no_crash(tmp_path):
    # Logger should create file if it doesn't exist
    logfile = tmp_path / "new.jsonl"
    logger = EventLogger(str(logfile))
    logger.log(turn=0, action="TEST", result="ok", feedback="")
    logger.close()
    assert os.path.isfile(str(logfile))


def test_replay_file_not_found(tmp_path):
    assert replay_log(str(tmp_path / "nope.jsonl")) == []
