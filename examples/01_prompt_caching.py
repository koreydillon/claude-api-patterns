"""
Prompt caching: drop input cost ~10x for repeated context.

The API caches a request prefix (tools -> system -> messages, in that order).
Any byte change anywhere in the prefix invalidates everything after it.
The first request pays the write premium (~1.25x); every subsequent request
that matches the prefix pays read price (~0.1x) for those tokens.

This example sends two requests sharing a large system prompt. The second
should report cache_read_input_tokens roughly equal to the system size.

Common silent invalidators to avoid:
  - datetime.now() / uuid in the system prompt
  - non-deterministic dict ordering (sort_keys=True when serializing)
  - tools that vary per request
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

MODEL = "claude-opus-4-7"

# A large, stable system prompt. In production this is your instructions,
# few-shot examples, retrieved docs, schemas. Anything frozen across calls.
SYSTEM_PROMPT = """You are a senior data engineering reviewer. You evaluate SQL
and pandas code for correctness, idempotency, and performance.

When reviewing, follow this rubric:
1. Idempotency: does the same input produce the same output every time?
2. Boundary handling: nulls, sentinels (e.g. 9999-12-31), empty inputs.
3. Window functions: are partition and order keys deterministic?
4. Type coercion: implicit casts that change behavior across engines.
5. Performance: full table scans, missing indexes, N+1 queries.

Output format: a numbered list of findings, each tagged [BLOCKING] or [NIT].
Cite the line number when possible. Skip findings that are stylistic.
""" * 5  # repeat to comfortably exceed the 1024-token cache minimum


def review(code_snippet: str) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": f"Review this:\n\n{code_snippet}"}],
    )
    return {
        "text": next(b.text for b in response.content if b.type == "text"),
        "usage": response.usage,
    }


if __name__ == "__main__":
    snippet_a = """
    SELECT user_id, MAX(created_at)
    FROM events
    GROUP BY user_id;
    """

    snippet_b = """
    INSERT INTO orders (id, total)
    SELECT id, total FROM staging_orders;
    """

    print("=== First call (cache write) ===")
    a = review(snippet_a)
    print(f"cache_creation_input_tokens: {a['usage'].cache_creation_input_tokens}")
    print(f"cache_read_input_tokens:     {a['usage'].cache_read_input_tokens}")
    print(f"input_tokens (uncached):     {a['usage'].input_tokens}")
    print()

    print("=== Second call (cache read) ===")
    b = review(snippet_b)
    print(f"cache_creation_input_tokens: {b['usage'].cache_creation_input_tokens}")
    print(f"cache_read_input_tokens:     {b['usage'].cache_read_input_tokens}")
    print(f"input_tokens (uncached):     {b['usage'].input_tokens}")
    print()

    if b["usage"].cache_read_input_tokens > 0:
        print("Cache hit on second call. System prefix served from cache.")
    else:
        print("No cache hit. Check for silent invalidators in the prefix.")
