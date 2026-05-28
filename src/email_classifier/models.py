from datetime import datetime

from pydantic import BaseModel, Field


class Email(BaseModel):
    message_id: str
    sender: str
    recipients: list[str] = Field(default_factory=list)
    subject: str = ""
    body: str = ""
    received_at: datetime | None = None


class Classification(BaseModel):
    label: str = Field(description="Short category label, e.g. work, personal, newsletter, spam.")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(default="", description="One-sentence justification.")
