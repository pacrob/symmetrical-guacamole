from typing import Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ..models import Classification
from .state import AgentState

SYSTEM_PROMPT = (
    "You are an email triage assistant. Read the email and assign a short "
    "category label (e.g. work, personal, newsletter, spam, transactional). "
    "Return your confidence as a number between 0 and 1 and a one-sentence reason."
)


def make_classify_node(model: BaseChatModel) -> Callable[[AgentState], dict]:
    structured = model.with_structured_output(Classification)

    def classify_node(state: AgentState) -> dict:
        email = state["email"]
        content = (
            f"Subject: {email.subject}\n"
            f"From: {email.sender}\n\n"
            f"{email.body}"
        )
        result = structured.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=content),
            ]
        )
        return {"classification": result}

    return classify_node
