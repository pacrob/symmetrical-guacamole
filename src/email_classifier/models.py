from typing import Literal

from pydantic import BaseModel, Field


class Email(BaseModel):
    message_id: str
    sender: str
    subject: str = ""
    body: str = ""


EmailLabel = Literal[
    "bug report",
    "question / support",
    "FYI / no action",
    "vendor / spam",
    "other / unclear",
]

PriorityLevel = Literal["low", "normal", "urgent"]


class Classification(BaseModel):
    label: EmailLabel = Field(description="Short category label")
    priority: PriorityLevel = Field(description="Triage urgency for the recipient.")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(default="", description="One- to two-sentence justification.")
    needs_review: bool = Field(
        default=False,
        description="System-set: true when confidence is below the review threshold.",
    )
