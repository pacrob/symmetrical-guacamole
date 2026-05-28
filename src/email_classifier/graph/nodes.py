from collections.abc import Callable
from typing import get_args

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ..models import Classification, EmailLabel, PriorityLevel
from .state import AgentState

LABELS = get_args(EmailLabel)
PRIORITIES = get_args(PriorityLevel)

SYSTEM_PROMPT = (
    "You are an email triage assistant. Read the email and:\n"
    f"- assign a category label (MUST BE one of: {', '.join(LABELS)})\n"
    f"- assign a priority (MUST BE one of: {', '.join(PRIORITIES)}); "
    "use 'urgent' for time-sensitive or blocking issues, 'low' for purely "
    "informational mail with no action needed, 'normal' otherwise\n"
    "Return your confidence as a number between 0 and 1 and a one-sentence reason."
)


def make_classify_node(model: BaseChatModel) -> Callable[[AgentState], dict]:
    structured = model.with_structured_output(Classification)

    def classify_node(state: AgentState) -> dict:
        email = state["email"]
        content = f"Subject: {email.subject}\nFrom: {email.sender}\n\n{email.body}"
        result = structured.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=content),
            ]
        )
        return {"classification": result}

    return classify_node
