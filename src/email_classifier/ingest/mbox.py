import mailbox
from datetime import datetime
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Iterator

from ..models import Email


class MboxSource:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def fetch(self) -> Iterator[Email]:
        box = mailbox.mbox(str(self.path))
        try:
            for msg in box:
                yield _to_email(msg)
        finally:
            box.close()


def _to_email(msg: Message) -> Email:
    to_headers = msg.get_all("To", []) + msg.get_all("Cc", [])
    return Email(
        message_id=msg.get("Message-ID", "").strip("<>"),
        sender=msg.get("From", ""),
        recipients=[addr for _, addr in getaddresses(to_headers) if addr],
        subject=msg.get("Subject", ""),
        body=_extract_body(msg),
        received_at=_parse_date(msg.get("Date")),
    )


def _extract_body(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.is_multipart():
                return _decode(part)
        return ""
    return _decode(msg)


def _decode(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return part.get_payload() or ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
