"""
main.py
House of AI — The Developer Council
Built by Christopher Hughes & The Good Neighbor Guard

Full pipeline: Architect (Claude) → Senior Engineer (GPT) → QA Tester (Gemini) → Synthesizer
Includes strict safety governors and a highly educational Kid Mode.
"""

import os
import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── consensus engine (memory_engine stubs are inside consensus_engine.py) ──
from consensus_engine import run_consensus_pipeline

app = FastAPI(title="House of AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
# Safety Governor & Mode Modifiers
# ---------------------------------------------------------------------------
SAFETY_GOVERNOR = (
    "\n\nCRITICAL SAFETY RULE: You are a system built under the Good Neighbor Guard ethos. "
    "You strictly build software applications. You MUST NEVER generate, encourage, or assist with "
    "adult, sexual, graphic real-world violence, illegal, or highly dangerous content. "
    "HOWEVER, cartoon violence, arcade game mechanics (like throwing objects, lasers, popping balloons, "
    "or silly enemies), and fantasy elements are 100% ALLOWED and encouraged. Do not falsely flag "
    "harmless game mechanics as safety violations. If the user asks for a game, build the game."
)

KID_MODE_MODIFIER = (
    "\n\nTONE OVERRIDE [KID MODE - EDUCATIONAL]: You are talking to a creative 10-year-old learning to "
    "build apps. Your primary goal is to TEACH them how coding works while keeping it fun! "
    "1. Explain what the code does using simple real-world analogies (e.g. 'variables are like magic boxes'). "
    "2. Add fun, easy-to-read comments INSIDE the code so they can follow along. "
    "3. Be highly encouraging, use emojis, and inspire them to become a future technologist. "
    "4. Keep the code real and functional — make the learning journey the best part!"
)

PRO_MODE_MODIFIER = (
    "\n\nTONE OVERRIDE [PRO MODE]: You are talking to an adult solo-developer. "
    "Be highly technical, concise, use industry-standard terminology. No fluff or excessive emojis."
)

# ---------------------------------------------------------------------------
# Base Agent Personas
# ---------------------------------------------------------------------------
BASE_ARCHITECT = (
    "You are the Chief Software Architect. The user will provide an app idea. "
    "Your job is strictly to design the architecture — you do NOT write functional code. "
    "Return a clear plan containing: "
    "1. The optimal tech stack. "
    "2. A complete folder/file structure. "
    "3. A step-by-step build plan for the Senior Engineer."
)

# CRITICAL FIX: Engineer is explicitly told to output ONE single HTML file.
# This is what enables the frontend Play button to work via Blob URL injection.
BASE_ENGINEER = (
    "You are the Senior Lead Developer. You receive an architecture plan and the user's original prompt. "
    "Your ONLY job is to write the actual, functional MVP code. "
    "\n\nCRITICAL OUTPUT FORMAT RULE: You MUST output the ENTIRE application as ONE SINGLE self-contained "
    "HTML file. ALL CSS must be inside a <style> tag in the <head>. ALL JavaScript must be inside a "
    "<script> tag at the bottom of the <body>. NO external files. NO CDN links that might fail. "
    "Inline everything. Wrap your entire output in a single ```html ... ``` code block. "
    "\n\nDo NOT give advice or suggestions — output FULL, WORKING, COPY-PASTE-READY code only."
)

BASE_QA = (
    "You are the QA Security Tester. You review the code written by the Senior Engineer. "
    "Your job is to break it. Look for security flaws, missing logic, infinite loops, and broken UI. "
    "Provide: "
    "1. A list of critical bugs (or 'NONE FOUND'). "
    "2. A list of security vulnerabilities (or 'NONE FOUND'). "
    "3. The exact corrected code snippets to fix any issues found. "
    "If the code is solid, return a PASS verdict."
)


def build_agent_prompt(base_prompt: str, app_mode: str) -> str:
    prompt = base_prompt + SAFETY_GOVERNOR
    if app_mode == "kid":
        prompt += KID_MODE_MODIFIER
    else:
        prompt += PRO_MODE_MODIFIER
    return prompt


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class TaskRequest(BaseModel):
    task: str
    context: str = ""
    namespace: str = "house_of_ai"
    phase: str = ""
    write_memory: bool = False   # Default False — memory_engine is optional
    app_mode: str = "kid"        # Passed from frontend toggle


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
async def call_claude(
    task: str, context: str, system_prompt: str, client: httpx.AsyncClient
) -> AgentResponse:
    try:
        messages = []
        if context:
            messages.append({"role": "user", "content": f"[CONTEXT]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood. I have reviewed the context."})
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
        return AgentResponse(
            agent="Architect (Claude)",
            response=r.json()["content"][0]["text"]
        )
    except Exception as e:
        return AgentResponse(agent="Architect (Claude)", response="", error=str(e))


async def call_gpt(
    task: str, context: str, system_prompt: str, client: httpx.AsyncClient
) -> AgentResponse:
    try:
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"[CONTEXT]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood. I have reviewed the context."})
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
        return AgentResponse(
            agent="Senior Engineer (GPT)",
            response=r.json()["choices"][0]["message"]["content"]
        )
    except Exception as e:
        return AgentResponse(agent="Senior Engineer (GPT)", response="", error=str(e))


async def call_gemini(
    task: str, context: str, system_prompt: str, client: httpx.AsyncClient
) -> AgentResponse:
    """
    Calls Gemini via REST — avoids the google-genai SDK sync/async conflict
    that caused the event loop to hang in the original code.
    """
    try:
        full_prompt = system_prompt + "\n\n"
        if context:
            full_prompt += f"[CONTEXT]\n{context}\n\n"
        full_prompt += task

        # Use REST directly — no SDK threading issues
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"maxOutputTokens": 4096},
            },
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
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

    # Build mode-aware prompts — app_mode flows from frontend toggle
    architect_prompt = build_agent_prompt(BASE_ARCHITECT, req.app_mode)
    engineer_prompt  = build_agent_prompt(BASE_ENGINEER,  req.app_mode)
    qa_prompt        = build_agent_prompt(BASE_QA,        req.app_mode)

    full_context = req.context or ""

    async with httpx.AsyncClient() as client:
        # Step 1 — Architect designs the plan (Claude)
        claude_res = await call_claude(req.task, full_context, architect_prompt, client)

        # Step 2 — Engineer writes the code based on the plan (GPT)
        engineer_context = full_context
        if claude_res.response:
            engineer_context += f"\n\n[ARCHITECT PLAN]\n{claude_res.response}"
        gpt_res = await call_gpt(req.task, engineer_context, engineer_prompt, client)

        # Step 3 — QA Tester reviews the code (Gemini)
        qa_context = engineer_context
        if gpt_res.response:
            qa_context += f"\n\n[ENGINEER CODE]\n{gpt_res.response}"
        gemini_res = await call_gemini(req.task, qa_context, qa_prompt, client)

        results = [claude_res, gpt_res, gemini_res]

        # Step 4 — Project Manager synthesizes final output
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
                "raw":               f"Consensus engine error: {e}",
                "summary":           "",
                "disagreements":     "",
                "final_decision":    "",
                "actionable_prompt": "",
                "memory_items":      [],
                "memory_writes":     [],
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


@app.get("/health")
async def health():
    return {"status": "House of AI live", "safety_layer": "active"}


# Serve frontend — index.html must be in a /static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
