"""
Token streaming for chat UIs.

Streaming gets first-token latency under a second and lets users see output
as it generates. The SDK helper accumulates the full Message for you, so
you can read usage stats and stop_reason after the stream completes.

For long outputs (max_tokens > ~16K), streaming is required - non-streaming
requests at that size will hit SDK HTTP timeouts.
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

MODEL = "claude-opus-4-7"


def stream_response(prompt: str) -> None:
    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        # text_stream yields just the text deltas, ignoring thinking blocks
        # and tool_use events. Use stream.events for fine-grained control.
        for text in stream.text_stream:
            print(text, end="", flush=True)

        # After the stream completes, get_final_message returns the same
        # Message object messages.create() would have produced.
        final = stream.get_final_message()

    print("\n")
    print(f"stop_reason:   {final.stop_reason}")
    print(f"input_tokens:  {final.usage.input_tokens}")
    print(f"output_tokens: {final.usage.output_tokens}")


if __name__ == "__main__":
    stream_response(
        "Write a short explanation of the producer-consumer pattern in three paragraphs."
    )
