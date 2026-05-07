"""
Batch API: 50% cost reduction for non-latency-sensitive workloads.

Submit up to 100,000 requests in one batch. Most batches finish within an
hour; the cap is 24h. Use it for:
  - Evals (run a prompt across a dataset)
  - Backfills (regenerate summaries for old records)
  - Classification jobs

Each request needs a custom_id you choose so you can correlate results
back to your data.
"""

import time
from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

MODEL = "claude-opus-4-7"

# Toy dataset. In production this would be loaded from a CSV / DB / S3.
REVIEWS = [
    ("rev-1", "The product arrived broken and support never replied."),
    ("rev-2", "Shipping was fast and the quality is solid for the price."),
    ("rev-3", "Decent but the instructions are unclear."),
    ("rev-4", "Replaced my old one and works exactly as advertised."),
]


def build_request(custom_id: str, review_text: str) -> Request:
    return Request(
        custom_id=custom_id,
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=64,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Classify this review as positive, negative, or neutral. "
                        f"Reply with one word only.\n\nReview: {review_text}"
                    ),
                }
            ],
        ),
    )


if __name__ == "__main__":
    print(f"Submitting {len(REVIEWS)} requests as a batch...")
    batch = client.messages.batches.create(
        requests=[build_request(cid, text) for cid, text in REVIEWS]
    )
    print(f"Batch id: {batch.id}")

    # Poll until done. Real apps should sleep longer; this is a toy demo.
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        print(f"  status: {batch.processing_status}, "
              f"processing: {batch.request_counts.processing}")
        time.sleep(15)

    print(f"\nDone. Succeeded: {batch.request_counts.succeeded}, "
          f"errored: {batch.request_counts.errored}")

    # Stream results. Each result has a custom_id matching what you submitted.
    print("\nResults:")
    for result in client.messages.batches.results(batch.id):
        if result.result.type == "succeeded":
            text = next(
                b.text for b in result.result.message.content if b.type == "text"
            ).strip()
            print(f"  {result.custom_id}: {text}")
        else:
            print(f"  {result.custom_id}: {result.result.type}")
