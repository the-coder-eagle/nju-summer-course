from dataclasses import dataclass, field

DEFAULT_DENYLIST = [
    "rm -rf", "sudo", "drop ",
    "| sh", "| bash",     # pipe-to-shell (catches curl/wget/etc)
    ":(){",                # fork bomb signature
    "chmod 777",
]

@dataclass
class Config:
    sandbox_root: str
    retry_budget: int = 5
    denylist: list = field(default_factory=lambda: list(DEFAULT_DENYLIST))
    warnlist: list = field(default_factory=list)
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com/v1"
    signals: list = field(default_factory=lambda: ["pytest"])

def load_config(data: dict) -> Config:
    return Config(
        sandbox_root=data["sandbox_root"],
        retry_budget=data.get("retry_budget", 5),
        denylist=data.get("denylist", list(DEFAULT_DENYLIST)),
        warnlist=data.get("warnlist", []),
        model=data.get("model", "deepseek-chat"),
        base_url=data.get("base_url", "https://api.deepseek.com/v1"),
        signals=data.get("signals", ["pytest"]),
    )
