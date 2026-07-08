from harness.config import load_config

def test_load_config_defaults_and_overrides():
    cfg = load_config({"sandbox_root": "/tmp/arena", "retry_budget": 3})
    assert cfg.sandbox_root == "/tmp/arena"
    assert cfg.retry_budget == 3
    assert "rm -rf" in cfg.denylist
    assert cfg.model == "deepseek-chat"
