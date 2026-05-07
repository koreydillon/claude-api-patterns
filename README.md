# claude-api-patterns

Six runnable patterns for building production apps on the Anthropic API. Each example is self-contained, uses the latest `claude-opus-4-7` model, and demonstrates one capability end-to-end.

## What's in here

| File | Pattern | When to use |
|---|---|---|
| `examples/01_prompt_caching.py` | System-prompt caching across requests | Repeated calls share a large prefix (docs, schemas, instructions) |
| `examples/02_tool_use_loop.py` | Manual agentic loop with multiple tools | You need fine-grained control over tool execution |
| `examples/03_batch_api.py` | Submit and poll a batch | Non-latency-sensitive workloads, 50% cost reduction |
| `examples/04_citations.py` | Document Q&A with grounded citations | Build trust by citing the source passage for each claim |
| `examples/05_extended_thinking.py` | Adaptive thinking + effort tuning | Hard reasoning tasks where you want the model to plan |
| `examples/06_streaming.py` | Token streaming for chat UIs | Real-time output, long responses |

## Why these patterns

These are the levers that move quality and cost most in real workloads:

- **Prompt caching** drops input cost ~10x for repeated context. Most teams leave it off because the API ergonomics aren't obvious. See `01_prompt_caching.py` for the right shape.
- **Manual tool loops** give you a place to log, gate, or sandbox tool calls that the SDK runner doesn't. The runner is great for prototypes; production agents usually need the manual loop.
- **Batch API** is the easiest 50% saving in the API. Use it for evals, backfills, classification jobs.
- **Citations** turn a Q&A app into something you can ship to compliance-sensitive users. Cheap to add, hard to retrofit.
- **Adaptive thinking** replaces fixed `budget_tokens`. The model decides how much to think; `effort` controls the ceiling.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add your ANTHROPIC_API_KEY to .env
```

## Run an example

```bash
python examples/01_prompt_caching.py
```

Each file prints what it's doing and why. Read the comment block at the top of any file before running.

## Models

All examples default to `claude-opus-4-7`. To swap in Sonnet 4.6 or Haiku 4.5, change the `MODEL` constant at the top of each file. See [model migration guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide) for parameter differences across versions.

## License

MIT
