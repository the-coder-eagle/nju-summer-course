"""Event logger: JSONL per-turn recording + replay."""
import json
import os


class EventLogger:
    def __init__(self, path: str):
        self._f = open(path, "a", encoding="utf-8")

    def log(self, turn: int, action: str, result: str, feedback: str):
        record = {"turn": turn, "action": action, "result": result, "feedback": feedback}
        self._f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._f.flush()

    def close(self):
        self._f.close()


def replay_log(path: str) -> list:
    """Read a JSONL event log, return list of parsed events.
    Malformed lines are silently skipped. Missing file returns []."""
    if not os.path.isfile(path):
        return []
    events = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip malformed lines
    return events
