from harness.llm.base import LLMInterface, LLMResponse


class MockLLM(LLMInterface):
    def __init__(self, script: list[str]):
        self._script = list(script)
        self._i = 0

    def complete(self, messages, tools=None) -> LLMResponse:
        if self._i >= len(self._script):
            raise StopIteration("MockLLM script exhausted")
        content = self._script[self._i]
        self._i += 1
        return LLMResponse(raw=content, content=content)
