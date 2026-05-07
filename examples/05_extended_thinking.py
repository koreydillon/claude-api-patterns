"""
Adaptive thinking and the effort parameter.

Claude 4.6 and 4.7 use adaptive thinking: the model decides when and how
much to think rather than spending a fixed budget you specify. The effort
parameter controls the ceiling.

Effort levels (Opus only supports max; Sonnet/Haiku error on it):
  low     - latency-sensitive, simple tasks
  medium  - balanced cost/quality
  high    - intelligence-sensitive work (recommended minimum on 4.7)
  xhigh   - coding and agentic loops on 4.7 (default in Claude Code)
  max     - correctness matters more than cost (Opus-tier only)

If you used `thinking={"type": "enabled", "budget_tokens": N}` on older
models, that returns 400 on Opus 4.7. Replace it with adaptive thinking.
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

MODEL = "claude-opus-4-7"

# A problem that benefits from planning before answering.
PROMPT = """A train leaves Phoenix at 9:00 AM heading east at 65 mph.
A second train leaves Albuquerque at 10:30 AM heading west at 80 mph.
Phoenix and Albuquerque are 460 miles apart.

At what time do the trains pass each other? Show your reasoning."""


def solve_at(effort: str) -> None:
    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": effort},
        messages=[{"role": "user", "content": PROMPT}],
    )

    thinking_text = ""
    answer_text = ""
    for block in response.content:
        if block.type == "thinking":
            thinking_text = block.thinking
        elif block.type == "text":
            answer_text = block.text

    print(f"=== effort={effort} ===")
    print(f"thinking summary ({len(thinking_text)} chars):")
    print((thinking_text[:300] + "...") if len(thinking_text) > 300 else thinking_text)
    print(f"\nanswer:\n{answer_text}")
    print(f"\nusage: input={response.usage.input_tokens}, "
          f"output={response.usage.output_tokens}\n")


if __name__ == "__main__":
    # Compare two effort levels on the same prompt.
    solve_at("medium")
    solve_at("high")
