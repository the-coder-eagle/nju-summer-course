from dataclasses import dataclass, field
from typing import Literal, Optional

@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[list] = None

@dataclass(frozen=True)
class ParseError:
    msg: str

@dataclass(frozen=True)
class ReadFile:
    path: str

@dataclass(frozen=True)
class EditFile:
    path: str
    old: str
    new: str

@dataclass(frozen=True)
class RunShell:
    cmd: str

@dataclass(frozen=True)
class RunTests:
    target: str

@dataclass(frozen=True)
class Finish:
    pass

Action = object  # union hint for consumers
def is_action(obj) -> bool:
    return isinstance(obj, (ReadFile, EditFile, RunShell, RunTests, Finish))
