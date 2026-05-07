"""
Manual agentic loop with multiple tools.

The SDK provides a higher-level tool runner (client.beta.messages.tool_runner)
that handles this for you. Use this manual pattern when you need to:
  - Log every tool call before executing it
  - Gate destructive tools behind confirmation
  - Run tools concurrently
  - Inject context between turns

The loop keeps going until stop_reason == "end_turn". Each iteration:
  1. Call the API with the running message history
  2. If Claude returned tool_use blocks, execute them
  3. Append the assistant turn AND a user turn with tool_result blocks
  4. Loop
"""

import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

MODEL = "claude-opus-4-7"

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Returns temperature in F and conditions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Phoenix, AZ'"}
            },
            "required": ["city"],
        },
    },
    {
        "name": "search_database",
        "description": "Search the customer order database. Returns matching order IDs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_email": {"type": "string"},
                "after_date": {"type": "string", "description": "ISO date, e.g. 2024-01-01"},
            },
            "required": ["customer_email"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> str:
    """Mock tool implementations. In production, dispatch to your real tools here."""
    if name == "get_weather":
        return json.dumps({"city": tool_input["city"], "temp_f": 78, "conditions": "sunny"})
    if name == "search_database":
        return json.dumps([{"order_id": "ord_42", "total": 199.00}])
    return f"Unknown tool: {name}"


def run(user_prompt: str, max_iterations: int = 8) -> str:
    messages: list = [{"role": "user", "content": user_prompt}]

    for _ in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(b.text for b in response.content if b.type == "text")

        # Append the assistant turn verbatim so tool_use IDs round-trip.
        messages.append({"role": "assistant", "content": response.content})

        # Execute every tool_use block in this turn and collect results.
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> calling {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"Loop did not terminate within {max_iterations} iterations")


if __name__ == "__main__":
    prompt = (
        "What's the weather in Phoenix, AZ? "
        "Also pull any orders for jane@example.com after 2024-01-01."
    )
    print(f"User: {prompt}\n")
    print("Assistant:", run(prompt))
