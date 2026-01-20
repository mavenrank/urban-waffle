import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

load_dotenv()

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def _resolve_credentials(model_name: str) -> Dict[str, str]:
    if model_name.startswith("gpt-"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        return {"api_key": api_key, "base_url": None}
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing")
    return {"api_key": api_key, "base_url": OPENROUTER_BASE}


class LLMClient:
    def __init__(self, model_name: str, temperature: float = 0.0, timeout: float = 30.0):
        creds = _resolve_credentials(model_name)
        self.model_name = model_name
        self.temperature = temperature
        self.timeout = timeout
        if creds["base_url"]:
            self.client = OpenAI(api_key=creds["api_key"], base_url=creds["base_url"], timeout=timeout)
        else:
            self.client = OpenAI(api_key=creds["api_key"], timeout=timeout)

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> ChatCompletion:
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
            temperature=self.temperature,
        )
