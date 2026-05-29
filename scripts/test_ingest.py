"""Classify emails from a .jsonl file and print results to the terminal.

Each line of the input file must be a JSON object matching the `Email` model.

Usage:
    uv run python scripts/test_ingest.py path/to/emails.jsonl
"""

import argparse
from collections.abc import Iterator
from pathlib import Path

from email_classifier.graph import build_graph
from email_classifier.llm import get_chat_model
from email_classifier.models import Email


def read_jsonl(path: Path) -> Iterator[Email]:
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield Email.model_validate_json(line)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to .jsonl file of emails")
    args = parser.parse_args()

    graph = build_graph(get_chat_model())

    for email in read_jsonl(args.path):
        result = graph.invoke({"email": email})
        c = result["classification"]
        print(f"--- {email.subject or '(no subject)'} ---")
        print(f"From:       {email.sender}")
        print(f"Priority:   {c.priority}")
        print(f"Label:      {c.label}")
        print(f"Confidence: {c.confidence:.2f}")
        print(f"Reason:     {c.reasoning}")
        print()


if __name__ == "__main__":
    main()
