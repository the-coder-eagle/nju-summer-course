from harness.llm.deepseek import DeepSeekClient


def test_complete_calls_api(monkeypatch):
    calls = {}

    def fake_post(url, *, headers=None, json=None, timeout=None):
        calls["url"] = url
        calls["auth"] = headers.get("Authorization")

        class R:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "EDIT a.py x->y"}}]}

        return R()

    monkeypatch.setattr("harness.llm.deepseek.httpx.post", fake_post)
    monkeypatch.setattr("harness.llm.deepseek.get_key", lambda: "sk-test")
    c = DeepSeekClient(model="deepseek-chat", base_url="https://api.deepseek.com/v1")
    r = c.complete(messages=[{"role": "user", "content": "fix"}])
    assert r.content == "EDIT a.py x->y"
    assert calls["auth"] == "Bearer sk-test"
