"""Classify emails from a .jsonl file and print results to the terminal.

Each line of the input file must be a JSON object matching the `Email` model.

Usage:
    uv run python scripts/test_ingest.py path/to/emails.jsonl
    uv run python scripts/test_ingest.py path/to/emails.jsonl --json
    uv run python scripts/test_ingest.py path/to/emails.jsonl --json results.json
"""

import argparse
import json
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
    parser.add_argument(
        "--json",
        nargs="?",
        const="output.json",
        default=None,
        metavar="FILE",
        help="Write classifications to FILE as JSON (default: output.json) instead of printing.",
    )
    args = parser.parse_args()

    graph = build_graph(get_chat_model())

    results: list[dict] = []
    for email in read_jsonl(args.path):
        result = graph.invoke({"email": email})
        c = result["classification"]
        if args.json:
            results.append({"message_id": email.message_id, **c.model_dump()})
        else:
            print(f"--- {email.subject or '(no subject)'} ---")
            print(f"From:       {email.sender}")
            print(f"Priority:   {c.priority}")
            print(f"Label:      {c.label}")
            print(f"Confidence: {c.confidence:.2f}")
            print(f"Reason:     {c.reasoning}")
            print()

    if args.json:
        out = Path(args.json)
        out.write_text(json.dumps(results, indent=2) + "\n")
        print(f"Wrote {len(results)} result(s) to {out}")


if __name__ == "__main__":
    main()
