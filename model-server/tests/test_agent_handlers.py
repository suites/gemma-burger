import pytest

from app.agent.handlers import (
    handle_complaint,
    handle_greeting,
    handle_history,
    handle_menu_qa,
    handle_order,
    handle_store_info,
)
from app.agent.state import AgentState, Intent


@pytest.fixture
def sample_state() -> AgentState:
    return {
        "messages": [{"role": "user", "content": "Hello!"}],
        "current_intent": Intent.GREETING.value,
        "final_response": "",
        "temperature": 0.7,
    }


def test_handle_greeting_returns_valid_prompt(sample_state):
    result = handle_greeting(sample_state)

    assert "final_response" in result
    assert isinstance(result["final_response"], str)
    assert len(result["final_response"]) > 0
    assert "temperature" in result
    assert result["temperature"] == 0.7


def test_handle_order_returns_valid_prompt(sample_state):
    sample_state["messages"] = [
        {"role": "user", "content": "I want a classic burger please"}
    ]

    result = handle_order(sample_state)

    assert "final_response" in result
    assert isinstance(result["final_response"], str)
    assert len(result["final_response"]) > 0
    assert "temperature" in result


def test_handle_menu_qa_returns_valid_prompt(sample_state):
    sample_state["messages"] = [
        {"role": "user", "content": "What are your most popular items?"}
    ]

    result = handle_menu_qa(sample_state)

    assert "final_response" in result
    assert isinstance(result["final_response"], str)
    assert "temperature" in result
    assert result["temperature"] == 0.5


def test_handle_store_info_returns_valid_prompt(sample_state):
    sample_state["messages"] = [
        {"role": "user", "content": "What are your opening hours?"}
    ]

    result = handle_store_info(sample_state)

    assert "final_response" in result
    assert isinstance(result["final_response"], str)
    assert "temperature" in result
    assert result["temperature"] == 0.2


def test_handle_complaint_returns_valid_prompt(sample_state):
    sample_state["messages"] = [
        {"role": "user", "content": "My burger is cold and the service is terrible!"}
    ]

    result = handle_complaint(sample_state)

    assert "final_response" in result
    assert isinstance(result["final_response"], str)
    assert "temperature" in result
    assert result["temperature"] == 0.2


def test_handle_history_with_conversation(sample_state):
    sample_state["messages"] = [
        {"role": "user", "content": "I want a burger"},
        {"role": "assistant", "content": "Great choice! Which one?"},
        {"role": "user", "content": "What did I order?"},
    ]

    result = handle_history(sample_state)

    assert "final_response" in result
    assert isinstance(result["final_response"], str)
    assert "temperature" in result
    assert result["temperature"] == 0.0


def test_handle_history_includes_conversation_context(sample_state):
    sample_state["messages"] = [
        {"role": "user", "content": "Classic burger please"},
        {"role": "assistant", "content": "One classic burger coming up!"},
        {"role": "user", "content": "What did I just order?"},
    ]

    result = handle_history(sample_state)

    prompt = result["final_response"]
    assert "USER:" in prompt or "user" in prompt.lower()
    assert "Classic burger" in prompt or "burger" in prompt.lower()
