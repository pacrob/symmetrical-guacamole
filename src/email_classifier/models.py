from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Email(BaseModel):
    id: str
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


class Classification(BaseModel):
    # label: str = Field(description="Short category label, e.g. work, personal, newsletter, spam.")
    label: EmailLabel = Field(description="Short category label")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(default="", description="One-sentence justification.")
