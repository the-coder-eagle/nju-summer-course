from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMResponse:
    raw: str
    content: str
    tool_calls: Optional[list] = field(default=None)


class LLMInterface:
    def complete(self, messages: list, tools: Optional[list] = None) -> LLMResponse:
        raise NotImplementedError
