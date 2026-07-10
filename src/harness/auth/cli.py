import getpass
from harness.auth import store


def status():
    print("DeepSeek key: " + ("set" if store.has_key() else "NOT set"))  # never echo value


def set_():
    v = getpass.getpass("DeepSeek API key (hidden): ")
    if v:
        store.set_key(v)
        print("stored.")


def update():
    set_()


def clear():
    store.clear_key()
    print("cleared.")
