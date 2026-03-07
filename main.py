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
    "You are Atlas the Architect. You receive a user prompt that may include a "
    "[NYMBLELOGIC TEMPLATE] spec. "
    "Your job is to write a SHORT, precise build plan (max 20 lines). "
    "If a template spec is provided: read it, note what to keep and what to customize. "
    "If no template: briefly outline the tech approach and component list. "
    "Do NOT write code. Do NOT pad with explanations. Be direct and specific."
)

# Byte the Builder — optimized for template-backed generation.
# Priority: customize known-good templates safely. Build from scratch only when no template matched.
BASE_ENGINEER = (
    "You are Byte the Builder — Senior Lead Developer for NymbleLogic. "
    "\n\nYour PRIMARY RULE: Output ONE single self-contained HTML file. "
    "ALL CSS inside <style>. ALL JS inside <script> at bottom of <body>. "
    "NO external CDN links. NO imports. Inline everything. "
    "Wrap output in a single ```html ... ``` block. No explanations outside the block. "
    "\n\nIF a [NYMBLELOGIC TEMPLATE] spec is present in your context: "
    "1. The template is already working. PRESERVE all logic listed under DO NOT TOUCH. "
    "2. ONLY customize the fields listed under SAFE TO CUSTOMIZE. "
    "3. Apply the user's requested changes (colors, content, theme, assets). "
    "4. Do NOT rewrite working mechanics from scratch — modify, not replace. "
    "5. Keep the win/lose/draw overlay logic exactly as specified. "
    "\n\nIF no template spec is present: "
    "Build a complete, working, polished single-file HTML app from scratch. "
    "Use vanilla JS only. Make it fully functional — no placeholder UI. "
    "\n\nQUALITY BAR: The output must be immediately playable or usable. "
    "No broken buttons. No missing game logic. No empty screens."
)

BASE_QA = (
    "You are Scout the Tester — QA engineer for NymbleLogic. "
    "Review the code from Byte the Builder. Be fast and specific. "
    "\n\nCheck for: "
    "1. Broken game logic or missing win/lose/draw states. "
    "2. JavaScript errors that would prevent the app from running. "
    "3. Buttons or interactions that do nothing. "
    "4. Infinite loops or performance issues. "
    "\n\nReturn: "
    "- VERDICT: PASS or FAIL "
    "- CRITICAL BUGS: (list or NONE) "
    "- FIXES: (exact code patches only — no full rewrites unless necessary) "
    "\n\nIf the code passes, say PASS and stop. Do not pad."
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



# ---------------------------------------------------------------------------
# Optional TTS endpoint — used by Nym in Kid Mode
# Fails gracefully if OPENAI_API_KEY not set
# ---------------------------------------------------------------------------
class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"

@app.post("/tts")
async def tts_endpoint(req: TTSRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="TTS not configured.")
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text required.")
    text = req.text.strip()[:300]  # Cap length
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": "tts-1", "input": text, "voice": req.voice},
                timeout=30,
            )
            r.raise_for_status()
            from fastapi.responses import Response
            return Response(content=r.content, media_type="audio/mpeg")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"TTS error: {e}")

@app.get("/health")
async def health():
    return {"status": "House of AI live", "safety_layer": "active"}


# Serve frontend — index.html must be in a /static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
