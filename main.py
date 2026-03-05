"""
main.py
The Good Neighbor Guard — House of AI
FastAPI backend: routes a task to Claude, GPT, and Gemini simultaneously,
then returns all three responses for side-by-side review.
"""

import os
import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="House of AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Config — set these as Render environment variables
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")

SYSTEM_PROMPT = (
    "You are a senior AI engineer on the Veracore fact-verification engine "
    "project for The Good Neighbor Guard. You are collaborating with two other "
    "AI systems (Claude and Gemini / GPT). Give your honest technical assessment. "
    "Be direct. Flag disagreements. Do not pad your response."
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class TaskRequest(BaseModel):
    task: str
    context: str = ""   # optional: paste prior phase output here


class AgentResponse(BaseModel):
    agent: str
    response: str
    error: str = ""


class HouseResponse(BaseModel):
    results: list[AgentResponse]
    consensus: str   # quick summary of where they agree / disagree


# ---------------------------------------------------------------------------
# LLM Callers
# ---------------------------------------------------------------------------
async def call_claude(task: str, context: str, client: httpx.AsyncClient) -> AgentResponse:
    try:
        messages = []
        if context:
            messages.append({"role": "user", "content": f"[CONTEXT FROM PRIOR PHASE]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood. I have the context."})
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
        data = r.json()
        text = data["content"][0]["text"]
        return AgentResponse(agent="Claude", response=text)
    except Exception as e:
        return AgentResponse(agent="Claude", response="", error=str(e))


async def call_gpt(task: str, context: str, client: httpx.AsyncClient) -> AgentResponse:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "user", "content": f"[CONTEXT FROM PRIOR PHASE]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood. I have the context."})
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
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return AgentResponse(agent="GPT", response=text)
    except Exception as e:
        return AgentResponse(agent="GPT", response="", error=str(e))


async def call_gemini(task: str, context: str, client: httpx.AsyncClient) -> AgentResponse:
    try:
        full_prompt = SYSTEM_PROMPT + "\n\n"
        if context:
            full_prompt += f"[CONTEXT FROM PRIOR PHASE]\n{context}\n\n"
        full_prompt += task

        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"maxOutputTokens": 2048},
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return AgentResponse(agent="Gemini", response=text)
    except Exception as e:
        return AgentResponse(agent="Gemini", response="", error=str(e))


async def build_consensus(results: list[AgentResponse], task: str, client: httpx.AsyncClient) -> str:
    """Ask Claude to do a quick meta-read: where do the three agree / conflict?"""
    try:
        summaries = "\n\n".join(
            f"=== {r.agent} ===\n{r.response or r.error}" for r in results
        )
        meta_prompt = (
            f"ORIGINAL TASK:\n{task}\n\n"
            f"THREE AI RESPONSES:\n{summaries}\n\n"
            "In 3-5 bullet points: where do they agree? Where do they conflict? "
            "What is the recommended action? Be blunt."
        )
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 512,
                "system": "You are a technical coordinator. Summarize AI consensus concisely.",
                "messages": [{"role": "user", "content": meta_prompt}],
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception as e:
        return f"Consensus engine error: {e}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.post("/consult", response_model=HouseResponse)
async def consult(req: TaskRequest):
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    async with httpx.AsyncClient() as client:
        claude_task, gpt_task, gemini_task = await asyncio.gather(
            call_claude(req.task, req.context, client),
            call_gpt(req.task, req.context, client),
            call_gemini(req.task, req.context, client),
        )
        results = [claude_task, gpt_task, gemini_task]
        consensus = await build_consensus(results, req.task, client)

    return HouseResponse(results=results, consensus=consensus)


@app.get("/health")
async def health():
    return {"status": "House is live"}


# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
