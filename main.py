"""
main.py
House of AI — The Developer Council
Full pipeline: Architect (Claude) → Senior Engineer (GPT) → QA Tester (Gemini) → Synthesizer
Includes strict safety governors for Kid/Pro modes.
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

app = FastAPI(title="House of AI")

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

# ---------------------------------------------------------------------------
# The Council Personas & Safety Governors
# ---------------------------------------------------------------------------
SAFETY_GOVERNOR = (
    "\n\nCRITICAL SAFETY RULE: You are a system built under the Good Neighbor Guard ethos. "
    "You strictly build software applications. You MUST NEVER generate, encourage, or assist with "
    "adult, sexual, violent, illegal, or highly dangerous content. If the user prompt violates this, "
    "you must immediately reject the request politely and suggest building a helpful app instead."
)

KID_MODE_MODIFIER = (
    "\n\nTONE OVERRIDE [KID MODE]: You are talking to a creative 10-year-old learning to build apps. "
    "Use simple language, be highly encouraging, use emojis, and explain complex coding concepts using "
    "fun real-world analogies (like building blocks or magic spells). Keep the code real, but the vibe fun."
)

PRO_MODE_MODIFIER = (
    "\n\nTONE OVERRIDE [PRO MODE]: You are talking to an adult solo-developer. "
    "Be highly technical, concise, use industry-standard terminology, and do not use fluff or excessive emojis."
)

BASE_ARCHITECT = (
    "You are the Chief Software Architect. The user will provide an app idea. "
    "Your job is strictly to design the architecture. You do not write the functional code. "
    "You must return a clear plan containing: "
    "1. The optimal tech stack. "
    "2. A complete folder and file structure. "
    "3. A step-by-step build plan for the Senior Engineer."
)

BASE_ENGINEER = (
    "You are the Senior Lead Developer. You will receive an architecture plan from the "
    "Architect and the user's original prompt. Your job is to write the actual, functional "
    "code for the MVP. You must return the exact code blocks for each required file, "
    "ensuring there are no placeholders and no missing logic. Write clean, production-ready code."
)

BASE_QA = (
    "You are the QA Security Tester. You will review the code written by the "
    "Senior Engineer. Your job is to break it. Look for security flaws, missing imports, "
    "infinite loops, and bad database calls. Provide: "
    "1. A list of critical bugs. "
    "2. A list of security vulnerabilities. "
    "3. The exact corrected code to fix these issues. "
    "If the code is perfect, return a 'PASS' verdict."
)


def build_agent_prompt(base_prompt: str, app_mode: str) -> str:
    prompt = base_prompt + SAFETY_GOVERNOR
    if app_mode == "kid":
        prompt += KID_MODE_MODIFIER
    else:
        prompt += PRO_MODE_MODIFIER
    return prompt


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class TaskRequest(BaseModel):
    task: str
    context: str = ""
    namespace: str = "house_of_ai"
    phase: str = ""
    write_memory: bool = True
    app_mode: str = "kid"  # Inherits from frontend toggle


class AgentResponse(BaseModel):
    agent: str
    response: str
    error: str = ""


class HouseResponse(BaseModel):
    results: list[AgentResponse]
    consensus: str
    summary: str = ""
    disagreements: str = ""
    final_decision: str = ""
    actionable_prompt: str = ""
    memory_items: list[str] = []
    memory_writes: list[dict] = []


class MemorySearchRequest(BaseModel):
    query: str
    namespace: str = "house_of_ai"


# ---------------------------------------------------------------------------
# LLM Callers 
# ---------------------------------------------------------------------------
async def call_claude(task: str, context: str, system_prompt: str, client: httpx.AsyncClient) -> AgentResponse:
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
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": messages,
            },
            timeout=120,
        )
        r.raise_for_status()
        return AgentResponse(agent="Architect (Claude)", response=r.json()["content"][0]["text"])
    except Exception as e:
        return AgentResponse(agent="Architect (Claude)", response="", error=str(e))


async def call_gpt(task: str, context: str, system_prompt: str, client: httpx.AsyncClient) -> AgentResponse:
    try:
        messages = [{"role": "system", "content": system_prompt}]
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
                "max_tokens": 4096,
                "messages": messages,
            },
            timeout=120,
        )
        r.raise_for_status()
        return AgentResponse(agent="Senior Engineer (GPT)", response=r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return AgentResponse(agent="Senior Engineer (GPT)", response="", error=str(e))


async def call_gemini(task: str, context: str, system_prompt: str, client: httpx.AsyncClient) -> AgentResponse:
    try:
        full_prompt = system_prompt + "\n\n"
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
        return AgentResponse(agent="QA Tester (Gemini)", response=text)
    except Exception as e:
        return AgentResponse(agent="QA Tester (Gemini)", response="", error=str(e))


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
        pass

    full_context = req.context
    if memory_context:
        full_context = memory_context + ("\n\n" + req.context if req.context else "")

    # Build dynamic prompts based on kid/pro mode
    architect_prompt = build_agent_prompt(BASE_ARCHITECT, req.app_mode)
    engineer_prompt  = build_agent_prompt(BASE_ENGINEER, req.app_mode)
    qa_prompt        = build_agent_prompt(BASE_QA, req.app_mode)

    async with httpx.AsyncClient() as client:
        # Step 1 — The Architect designs the plan (Claude)
        claude_res = await call_claude(req.task, full_context, architect_prompt, client)

        # Step 2 — The Engineer writes the code based on the plan (GPT)
        engineer_context = f"{full_context}\n\n[ARCHITECT PLAN]\n{claude_res.response}"
        gpt_res = await call_gpt(req.task, engineer_context, engineer_prompt, client)

        # Step 3 — The QA Tester reviews the code (Gemini)
        qa_context = f"{engineer_context}\n\n[ENGINEER CODE]\n{gpt_res.response}"
        gemini_res = await call_gemini(req.task, qa_context, qa_prompt, client)

        results = [claude_res, gpt_res, gemini_res]

        # Step 4 — Project Manager synthesizes the final output
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
    return {"status": "House of AI live", "safety_layer": "active"}


# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
