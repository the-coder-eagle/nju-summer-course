import httpx
from harness.llm.base import LLMInterface, LLMResponse
from harness.auth.store import get_key


class DeepSeekClient(LLMInterface):
    def __init__(self, model="deepseek-chat", base_url="https://api.deepseek.com/v1"):
        self.model = model
        self.base_url = base_url

    def complete(self, messages, tools=None) -> LLMResponse:
        key = get_key()
        if not key:
            raise RuntimeError("DeepSeek key not set; run: harness auth set")
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        return LLMResponse(raw=str(data), content=content)
