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

## Roadmap

Tracked against the project's functional requirements. `[x]` done, `[~]` partial, `[ ]` not started.

### Must (defines done)

- [x] **FR-1** — Accept a single email from a local source. ([`MboxSource`](src/email_classifier/ingest/mbox.py), JSONL via [scripts/test_ingest.py](scripts/test_ingest.py))
- [x] **FR-2** — Classify into exactly one category. `EmailLabel` `Literal` + `with_structured_output` enforce the set.
- [x] **FR-3** — Assign a priority (`low` / `normal` / `urgent`). `PriorityLevel` `Literal` + `priority` field on `Classification`; `with_structured_output` enforces the set, prompt advertises the values.
- [x] **FR-4** — One-to-two sentence rationale. `reasoning` field on `Classification`; prompt asks for "one- to two-sentence rationale" and the field description matches.
- [x] **FR-5** — Emit results as structured JSON with a stable schema. `Classification` is the schema; [scripts/test_ingest.py](scripts/test_ingest.py) `--json [FILE]` writes a JSON array of `{message_id, label, priority, confidence, reasoning}` records (defaults to `output.json`).
- [x] **FR-6** — Process a batch from a file in one run. (JSONL script iterates the file.)

### Should (expected if time allows)

- [x] **FR-7** — Junk / ambiguous bucket. `other / unclear` exists in `EmailLabel`; structured output guarantees the LLM can always pick a valid value.
- [x] **FR-8** — Flag low-confidence decisions for human review. `review_threshold: float = 0.7` in `Settings`; classify node sets `needs_review = confidence < threshold` on `Classification`. Console output shows `[NEEDS REVIEW]` marker; JSON output includes the flag.

### Could (nice to have)

- [ ] **FR-9** — Configurable categories without code changes. Move labels + descriptions into a config file (e.g. `labels.yaml`) and load them at startup. Note the tradeoff: dropping the `Literal` type loses static narrowing (mypy / IDE autocomplete) in exchange for runtime configurability — likely worth a small `StrEnum`-or-set-based validator pattern instead.
- [ ] **FR-10** — Suggest a one-line draft reply for routine categories. Adds a second graph node (`draft_node`) that runs conditionally (e.g. only for `question / support` with confidence ≥ threshold), and a `draft: str | None` field on the output. First real use of LangGraph's conditional edges.
