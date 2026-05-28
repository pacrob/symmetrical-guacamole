from typing import NotRequired, TypedDict

from ..models import Classification, Email


class AgentState(TypedDict):
    email: Email
    classification: NotRequired[Classification]
