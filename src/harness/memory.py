import os


def load_conventions(project_dir: str) -> str:
    p = os.path.join(project_dir, "CONVENTIONS.md")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return ""


def compress_history(history: list, max_messages: int = 20) -> list:
    """Truncate history to max_messages, keeping first entry for context.
    If truncation needed, inserts a notice about omitted messages."""
    if len(history) <= max_messages:
        return list(history)
    if max_messages <= 2:
        return list(history[-max_messages:])

    first = history[0]
    omitted = len(history) - max_messages
    notice = ("user", f"[{omitted} earlier messages omitted for brevity]")
    tail = list(history[-(max_messages - 2):])
    return [first, notice] + tail
