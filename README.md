# email-classifier

A small email triage agent built with **LangGraph**, **LangChain**, and **Pydantic**. Reads emails from a source (an `.mbox` file or a `.jsonl` dump), runs each one through a single-node classification graph, and returns a structured `Classification` (label, confidence, reasoning).

This is primarily a learning project — the focus is on clean separation of concerns so the pieces can grow independently (more sources, more graph nodes, swap providers) without rewriting each other.

## Architecture

```
src/email_classifier/
├── models.py           # Pydantic: Email, Classification, EmailLabel (Literal)
├── config.py           # pydantic-settings: API keys + model name from env / .env
├── llm.py              # get_chat_model() factory (currently ChatOpenAI)
├── ingest/
│   ├── base.py         # EmailSource protocol: fetch() -> Iterable[Email]
│   └── mbox.py         # MboxSource: read .mbox via stdlib `mailbox`
└── graph/
    ├── state.py        # AgentState (TypedDict): {email, classification?}
    ├── nodes.py        # make_classify_node(model) -> graph node
    └── builder.py      # build_graph(model) -> compiled StateGraph
```

**Key boundaries:**

- **`Email` is the durable record; `AgentState` is graph scratch.** Transient agent fields (label, confidence, reasoning, tool outputs) live in state, not on `Email`. Swap the graph implementation without changing the email model.
- **Sources are plug-in.** Anything implementing `EmailSource.fetch() -> Iterable[Email]` works. `MboxSource` is the dev-time source; IMAP / Gmail API drop in later behind the same protocol.
- **LLM is injected.** Nodes take a model via factory (`make_classify_node(model)`), so tests don't need a real API key and providers can be swapped in [llm.py](src/email_classifier/llm.py) without touching graph code.
- **Config at the edges.** `Settings` (pydantic-settings) reads `.env` and shell env vars; library code never touches `os.environ`.

## Setup

```bash
uv sync                       # install runtime + dev deps
cp .env.example .env          # then fill in OPENAI_API_KEY
```

The project uses Python 3.13 and OpenAI (`gpt-4o-mini`) by default. To switch to Anthropic, uncomment the `ChatAnthropic` block in [llm.py](src/email_classifier/llm.py) and adjust `DEFAULT_MODEL` in [config.py](src/email_classifier/config.py).

## Usage

### Classify a JSONL file of emails

```bash
uv run python scripts/test_ingest.py path/to/emails.jsonl
```

Each line of the file must be a JSON object matching the `Email` model:

```jsonl
{"message_id": "1", "sender": "alice@example.com", "subject": "Bug in login", "body": "It crashes."}
{"message_id": "2", "sender": "bob@example.com", "subject": "Lunch?", "body": "Want to grab lunch?"}
```

Output per email:

```
--- Bug in login ---
From:       alice@example.com
Label:      bug report
Confidence: 0.92
Reason:     Reports a crash in the login feature.
```

### Use the pipeline programmatically

```python
from email_classifier.graph import build_graph
from email_classifier.ingest import MboxSource
from email_classifier.llm import get_chat_model

graph = build_graph(get_chat_model())
for email in MboxSource("inbox.mbox").fetch():
    result = graph.invoke({"email": email})
    print(email.subject, "->", result["classification"])
```

## Labels

Defined as a `Literal` in [models.py](src/email_classifier/models.py); the LLM is constrained to one of:

- `bug report`
- `question / support`
- `FYI / no action`
- `vendor / spam`
- `other / unclear`

Add or change labels there and the system prompt + structured-output schema pick them up automatically.

## Development

```bash
make lint       # ruff check + format check
make fix        # ruff autofix + format
make test       # pytest
make check      # lint + test (pre-commit gate)
```

Tests use a fake chat model — no API key required to run the suite.
