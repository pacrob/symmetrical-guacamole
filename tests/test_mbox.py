import mailbox
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

from email_classifier.ingest.mbox import (
    MboxSource,
    _extract_body,
    _parse_date,
    _to_email,
)


def _make_msg(
    *,
    subject: str = "hi",
    sender: str = "alice@example.com",
    body: str = "hello",
    message_id: str = "<abc@example.com>",
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["Message-ID"] = message_id
    msg.set_content(body)
    return msg


def _write_mbox(path: Path, messages: list[EmailMessage]) -> None:
    box = mailbox.mbox(str(path))
    try:
        for msg in messages:
            box.add(msg)
    finally:
        box.close()


def test_fetch_yields_email_per_message(tmp_path: Path) -> None:
    path = tmp_path / "inbox.mbox"
    _write_mbox(
        path,
        [
            _make_msg(subject="one"),
            _make_msg(subject="two", message_id="<def@example.com>"),
        ],
    )

    emails = list(MboxSource(path).fetch())

    assert [e.subject for e in emails] == ["one", "two"]
    assert emails[0].sender == "alice@example.com"
    assert emails[0].body.strip() == "hello"


def test_to_email_strips_message_id_brackets() -> None:
    assert _to_email(_make_msg(message_id="<xyz@host>")).message_id == "xyz@host"


def test_to_email_tolerates_missing_headers() -> None:
    msg = EmailMessage()
    msg.set_content("body only")

    email = _to_email(msg)

    assert email.message_id == ""
    assert email.sender == ""


def test_extract_body_prefers_text_plain_in_multipart() -> None:
    msg = EmailMessage()
    msg.set_content("the plain part")
    msg.add_alternative("<p>the html part</p>", subtype="html")

    assert "the plain part" in _extract_body(msg)


def test_parse_date_handles_missing_and_malformed() -> None:
    assert _parse_date(None) is None
    assert _parse_date("") is None
    assert _parse_date("not a date") is None
