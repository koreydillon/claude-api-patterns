"""
Document Q&A with grounded citations.

Pass a document with citations enabled, ask a question, and Claude returns
citation blocks alongside its answer pointing at the exact source passage.
This is what turns a Q&A app into something compliance-sensitive users
will trust.

The document can be a PDF (base64 or URL), plain text, or a "content"
document (an array of text blocks the API treats as page-like chunks).
This example uses the content variant for clarity.
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

MODEL = "claude-opus-4-7"

# A toy "policy document" split into chunks. Each chunk gets its own citation.
POLICY_CHUNKS = [
    "Section 1. Returns. All hardware items may be returned within 30 days "
    "of delivery for a full refund. Software licenses are non-refundable "
    "once activated.",
    "Section 2. Warranty. Hardware is covered by a one-year limited warranty "
    "against manufacturing defects. The warranty does not cover damage from "
    "spills, drops, or unauthorized modifications.",
    "Section 3. Support. Standard support is available Monday through Friday "
    "from 9 AM to 6 PM Eastern. Enterprise customers receive 24/7 support "
    "with a four-hour response SLA.",
]


def ask(question: str) -> None:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "content",
                            "content": [{"type": "text", "text": chunk} for chunk in POLICY_CHUNKS],
                        },
                        "title": "Customer Policy v1.0",
                        "citations": {"enabled": True},
                    },
                    {"type": "text", "text": question},
                ],
            }
        ],
    )

    print(f"Q: {question}\n")
    for block in response.content:
        if block.type != "text":
            continue
        print(block.text)
        for cite in (block.citations or []):
            # Citation type depends on document source: content_block_location,
            # page_location, or char_location. All carry cited_text.
            cited = getattr(cite, "cited_text", None)
            if cited:
                print(f"  [cite] {cited!r}")
    print()


if __name__ == "__main__":
    ask("Can I return a software license after activating it?")
    ask("What's the SLA for enterprise support?")
