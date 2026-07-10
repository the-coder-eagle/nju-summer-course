from harness.llm.mock import MockLLM
from harness.llm.base import LLMResponse


def test_mock_returns_scripted_then_finish():
    llm = MockLLM(script=['EDIT a.py old->new', 'FINISH'])
    r1 = llm.complete(messages=[])
    assert r1.content == 'EDIT a.py old->new'
    r2 = llm.complete(messages=[])
    assert r2.content == 'FINISH'


def test_mock_raises_when_exhausted():
    import pytest
    llm = MockLLM(script=['only'])
    llm.complete([])
    with pytest.raises(StopIteration):
        llm.complete([])
