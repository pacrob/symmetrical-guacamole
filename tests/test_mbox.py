import mailbox
from datetime import datetime, timezone
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
    to: str = "bob@example.com",
    body: str = "hello",
    message_id: str = "<abc@example.com>",
    date: str = "Mon, 1 Jan 2024 12:00:00 +0000",
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg["Message-ID"] = message_id
    msg["Date"] = date
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
    assert emails[0].received_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_to_email_strips_message_id_brackets() -> None:
    assert _to_email(_make_msg(message_id="<xyz@host>")).message_id == "xyz@host"


def test_to_email_combines_to_and_cc() -> None:
    msg = _make_msg(to="bob@example.com, carol@example.com")
    msg["Cc"] = "dave@example.com"

    assert _to_email(msg).recipients == [
        "bob@example.com",
        "carol@example.com",
        "dave@example.com",
    ]


def test_to_email_tolerates_missing_headers() -> None:
    msg = EmailMessage()
    msg.set_content("body only")

    email = _to_email(msg)

    assert email.message_id == ""
    assert email.sender == ""
    assert email.recipients == []
    assert email.received_at is None


def test_extract_body_prefers_text_plain_in_multipart() -> None:
    msg = EmailMessage()
    msg.set_content("the plain part")
    msg.add_alternative("<p>the html part</p>", subtype="html")

    assert "the plain part" in _extract_body(msg)


def test_parse_date_handles_missing_and_malformed() -> None:
    assert _parse_date(None) is None
    assert _parse_date("") is None
    assert _parse_date("not a date") is None
