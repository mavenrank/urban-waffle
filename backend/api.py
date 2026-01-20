import traceback
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_loop import run_agent

load_dotenv()

app = FastAPI(title="Pagila RAG (no LangChain)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = "mistralai/mistral-7b-instruct:free"


class QueryResponse(BaseModel):
    response: str
    metadata: Optional[dict] = None


@app.get("/")
def root():
    return {"message": "Pagila RAG backend running"}


@app.get("/models")
def models():
    models_list = [
        {"id": "gpt-4o-mini", "name": "OpenAI GPT-4o Mini"},
        {"id": "gpt-3.5-turbo", "name": "OpenAI GPT-3.5 Turbo"},
        {"id": "gpt-4o", "name": "OpenAI GPT-4o"},
    ]
    try:
        resp = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            free_models = [
                m
                for m in data
                if m.get("pricing", {}).get("prompt") == "0"
                and m.get("pricing", {}).get("completion") == "0"
            ]
            free_models.sort(key=lambda m: m.get("name", ""))
            models_list.extend(free_models)
    except Exception:  # noqa: BLE001
        # Swallow fetch issues; the OpenAI list still works
        pass
    return {"models": models_list}


@app.post("/chat", response_model=QueryResponse)
def chat(request: QueryRequest):
    try:
        response, metadata = run_agent(request.query, request.model or "mistralai/mistral-7b-instruct:free")
        return QueryResponse(response=response, metadata=metadata)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        msg = str(exc)
        status = 429 if "429" in msg or "Rate" in msg else 500
        raise HTTPException(status_code=status, detail=msg)
