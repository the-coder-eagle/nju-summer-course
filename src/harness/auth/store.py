import keyring

SERVICE = "harness.deepseek"
ACCOUNT = "default"


def get_key() -> str | None:
    return keyring.get_password(SERVICE, ACCOUNT)


def has_key() -> bool:
    return get_key() is not None


def set_key(value: str):
    keyring.set_password(SERVICE, ACCOUNT, value)


def clear_key():
    try:
        keyring.delete_password(SERVICE, ACCOUNT)
    except keyring.errors.PasswordDeleteError:
        pass
