import os


def load_conventions(project_dir: str) -> str:
    p = os.path.join(project_dir, "CONVENTIONS.md")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return ""
