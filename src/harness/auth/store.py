import os
import keyring

SERVICE = "harness.deepseek"
ACCOUNT = "default"


def get_key() -> str | None:
    # 1. Try OS keyring (Windows/macOS/Linux desktop)
    key = keyring.get_password(SERVICE, ACCOUNT)
    if key:
        return key
    # 2. Fall back to env var (Docker/Render/CI)
    return os.environ.get("DEEPSEEK_API_KEY")


def has_key() -> bool:
    return get_key() is not None


def set_key(value: str):
    try:
        keyring.set_password(SERVICE, ACCOUNT, value)
    except keyring.errors.KeyringError:
        # In Docker/headless, keyring may not be available — use env var
        pass


def clear_key():
    try:
        keyring.delete_password(SERVICE, ACCOUNT)
    except (keyring.errors.PasswordDeleteError, keyring.errors.KeyringError):
        pass
