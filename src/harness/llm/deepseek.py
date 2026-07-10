import httpx
from dataclasses import asdict
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
        # Convert Message dataclasses to plain dicts, strip None fields
        msgs = []
        for m in messages:
            if hasattr(m, 'role'):
                d = asdict(m)
                d = {k: v for k, v in d.items() if v is not None}
                msgs.append(d)
            else:
                msgs.append(m)
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": msgs},
            timeout=60,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"DeepSeek API {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        return LLMResponse(raw=str(data), content=content)
