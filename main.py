"""
main.py
The Good Neighbor Guard — House of AI v2
Full pipeline: Claude + GPT + Gemini → Consensus Synthesizer → Pinecone Memory
"""

import os
import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai as google_genai

from consensus_engine import run_consensus_pipeline
from memory_engine import memory_search, memory_pack_for_prompt

app = FastAPI(title="House of AI v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Config — Render environment variables
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")

SYSTEM_PROMPT = (
    "You are a senior AI engineer on the Veracore fact-verification engine "
    "project for The Good Neighbor Guard. You are collaborating with two other "
    "AI systems. Give your honest technical assessment. "
    "Be direct. Flag disagreements. Do not pad your response."
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class TaskRequest(BaseModel):
    task: str
    context: str = ""
    namespace: str = "veracore"   # veracore | lylo | general
    phase: str = ""
    write_memory: bool = True


class AgentResponse(BaseModel):
    agent: str
    response: str
    error: str = ""


class HouseResponse(BaseModel):
    results: list[AgentResponse]
    # Legacy simple consensus (kept for UI backward compat)
    consensus: str
    # New structured consensus
    summary: str = ""
    disagreements: str = ""
    final_decision: str = ""
    actionable_prompt: str = ""
    memory_items: list[str] = []
    memory_writes: list[dict] = []


class MemorySearchRequest(BaseModel):
    query: str
    namespace: str = "veracore"


# ---------------------------------------------------------------------------
# LLM Callers
# ---------------------------------------------------------------------------
async def call_claude(task: str, context: str, client: httpx.AsyncClient) -> AgentResponse:
    try:
        messages = []
        if context:
            messages.append({"role": "user", "content": f"[CONTEXT]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood."})
        messages.append({"role": "user", "content": task})

        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 2048,
                "system": SYSTEM_PROMPT,
                "messages": messages,
            },
            timeout=60,
        )
        r.raise_for_status()
        return AgentResponse(agent="Claude", response=r.json()["content"][0]["text"])
    except Exception as e:
        return AgentResponse(agent="Claude", response="", error=str(e))


async def call_gpt(task: str, context: str, client: httpx.AsyncClient) -> AgentResponse:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "user", "content": f"[CONTEXT]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood."})
        messages.append({"role": "user", "content": task})

        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "max_tokens": 2048,
                "messages": messages,
            },
            timeout=60,
        )
        r.raise_for_status()
        return AgentResponse(agent="GPT", response=r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return AgentResponse(agent="GPT", response="", error=str(e))


async def call_gemini(task: str, context: str, client: httpx.AsyncClient) -> AgentResponse:
    try:
        full_prompt = SYSTEM_PROMPT + "\n\n"
        if context:
            full_prompt += f"[CONTEXT]\n{context}\n\n"
        full_prompt += task

        def _sync_call():
            gclient = google_genai.Client(api_key=GEMINI_API_KEY)
            response = gclient.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )
            return response.text

        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, _sync_call)
        return AgentResponse(agent="Gemini", response=text)
    except Exception as e:
        return AgentResponse(agent="Gemini", response="", error=str(e))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.post("/consult", response_model=HouseResponse)
async def consult(req: TaskRequest):
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    # Inject relevant memory into context if available
    memory_context = ""
    try:
        memory_context = await memory_pack_for_prompt(req.task, req.namespace)
    except Exception:
        pass  # Memory failure never blocks a consult

    full_context = req.context
    if memory_context:
        full_context = memory_context + ("\n\n" + req.context if req.context else "")

    async with httpx.AsyncClient() as client:
        # Step 1 — fire all three in parallel
        claude_res, gpt_res, gemini_res = await asyncio.gather(
            call_claude(req.task, full_context, client),
            call_gpt(req.task, full_context, client),
            call_gemini(req.task, full_context, client),
        )
        results = [claude_res, gpt_res, gemini_res]

        # Step 2 — consensus synthesizer
        try:
            consensus_data = await run_consensus_pipeline(
                task=req.task,
                claude_response=claude_res.response,
                gpt_response=gpt_res.response,
                gemini_response=gemini_res.response,
                client=client,
                namespace=req.namespace,
                phase=req.phase,
                write_memory=req.write_memory,
            )
        except Exception as e:
            consensus_data = {
                "raw": f"Consensus engine error: {e}",
                "summary": "",
                "disagreements": "",
                "final_decision": "",
                "actionable_prompt": "",
                "memory_items": [],
                "memory_writes": [],
            }

    return HouseResponse(
        results=results,
        consensus=consensus_data["raw"],
        summary=consensus_data["summary"],
        disagreements=consensus_data["disagreements"],
        final_decision=consensus_data["final_decision"],
        actionable_prompt=consensus_data["actionable_prompt"],
        memory_items=consensus_data["memory_items"],
        memory_writes=consensus_data["memory_writes"],
    )


@app.post("/memory/search")
async def search_memory(req: MemorySearchRequest):
    try:
        results = await memory_search(req.query, req.namespace)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "House of AI v2 live"}


# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
