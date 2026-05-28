from typing import Any, get_args

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from email_classifier.graph import build_graph
from email_classifier.graph.nodes import SYSTEM_PROMPT, make_classify_node
from email_classifier.models import Classification, Email, PriorityLevel


class _RecordingStructured:
    def __init__(self, response: Classification) -> None:
        self.response = response
        self.calls: list[list[Any]] = []

    def invoke(self, messages: list[Any]) -> Classification:
        self.calls.append(messages)
        return self.response


class _FakeModel:
    def __init__(self, response: Classification) -> None:
        self.structured = _RecordingStructured(response)

    def with_structured_output(self, schema: Any) -> _RecordingStructured:
        return self.structured


def _email(**overrides: Any) -> Email:
    defaults: dict[str, Any] = dict(
        message_id="m1",
        sender="alice@example.com",
        subject="Lunch?",
        body="Want to grab lunch tomorrow?",
    )
    defaults.update(overrides)
    return Email(**defaults)


def test_classify_node_returns_classification_update() -> None:
    expected = Classification(
        label="FYI / no action",
        priority="low",
        confidence=0.9,
        reasoning="lunch invite",
    )
    model = _FakeModel(expected)
    node = make_classify_node(model)  # type: ignore[arg-type]

    update = node({"email": _email()})

    assert update == {"classification": expected}


def test_classify_node_prompts_with_email_content() -> None:
    model = _FakeModel(Classification(label="other / unclear", priority="normal", confidence=0.0))
    node = make_classify_node(model)  # type: ignore[arg-type]

    node(
        {
            "email": _email(
                subject="Project plan",
                sender="bob@work.com",
                body="See attached.",
            )
        }
    )

    [messages] = model.structured.calls
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content == SYSTEM_PROMPT
    assert isinstance(messages[1], HumanMessage)
    human = messages[1].content
    assert "Project plan" in human
    assert "bob@work.com" in human
    assert "See attached." in human


def test_build_graph_runs_classify_end_to_end() -> None:
    expected = Classification(
        label="vendor / spam",
        priority="low",
        confidence=0.7,
        reasoning="bulk send",
    )
    graph = build_graph(_FakeModel(expected))  # type: ignore[arg-type]

    result = graph.invoke({"email": _email()})

    assert result["classification"] == expected
    assert "classify" in graph.get_graph().nodes


def test_system_prompt_advertises_every_priority_value() -> None:
    for priority in get_args(PriorityLevel):
        assert priority in SYSTEM_PROMPT


def test_classification_rejects_unknown_priority() -> None:
    with pytest.raises(ValidationError):
        Classification(
            label="bug report",
            priority="critical",  # type: ignore[arg-type]
            confidence=0.5,
        )
