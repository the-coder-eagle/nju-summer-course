from lib import add


def test_add_returns_int():
    result = add(2, 3)
    assert result == 5
    assert isinstance(result, int)
