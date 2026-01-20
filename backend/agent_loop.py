import json
import time
from typing import Dict, List, Tuple

from llm_client import LLMClient
from prompts import SYSTEM_PROMPT
from tools import TOOLS, call_tool


def _as_assistant_message(message) -> Dict:
    tool_calls = []
    if message.tool_calls:
        for tc in message.tool_calls:
            tool_calls.append(
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
            )
    return {"role": "assistant", "content": message.content or "", "tool_calls": tool_calls}


def _ensure_final_prefix(content: str) -> str:
    lowered = content.lower().strip()
    if lowered.startswith("final answer:"):
        return content
    return f"Final Answer: {content}" if content else "Final Answer: (no content)"


def run_agent(user_query: str, model_name: str = "mistralai/mistral-7b-instruct:free", max_steps: int = 5) -> Tuple[str, Dict[str, float]]:
    messages: List[Dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    client = LLMClient(model_name)
    start = time.time()

    for _ in range(max_steps):
        completion = client.chat(messages=messages, tools=TOOLS)
        message = completion.choices[0].message

        if message.tool_calls:
            assistant_msg = _as_assistant_message(message)
            messages.append(assistant_msg)
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                result = call_tool(tc.function.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )
            continue

        content = _ensure_final_prefix(message.content or "")
        duration = time.time() - start
        return content, {"model": model_name, "duration": round(duration, 2)}

    duration = time.time() - start
    return (
        "Final Answer: I could not complete the request within the step limit. Please try again.",
        {"model": model_name, "duration": round(duration, 2)},
    )
