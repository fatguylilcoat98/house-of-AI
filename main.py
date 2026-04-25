"""
main.py
NymbleLogic — House of AI
Built by Christopher Hughes & The Good Neighbor Guard

Pipeline: Architect (Claude) → Builder (GPT) → Scout QA (Gemini) → Fix Loop → Synthesizer
"""

import os
import re
import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import json

from consensus_engine import run_consensus_pipeline

app = FastAPI(title="NymbleLogic — House of AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")

MAX_FIX_ATTEMPTS = 2  # Scout → fix loop max retries

# ---------------------------------------------------------------------------
# Safety Governor
# ---------------------------------------------------------------------------
SAFETY_GOVERNOR = (
    "\n\nCRITICAL SAFETY RULE: You are a system built under the Good Neighbor Guard ethos. "
    "You strictly build software applications. You MUST NEVER generate, encourage, or assist with "
    "adult, sexual, graphic real-world violence, illegal, or highly dangerous content. "
    "HOWEVER, cartoon violence, arcade game mechanics (like throwing objects, lasers, popping balloons, "
    "or silly enemies), and fantasy elements are 100% ALLOWED and encouraged. "
    "Do not falsely flag harmless game mechanics as safety violations. "
    "If the user asks for a game, build the game."
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
# Agent Personas
# ---------------------------------------------------------------------------
BASE_ARCHITECT = (
    "You are Atlas the Architect. You receive a user prompt that may include a "
    "[NYMBLELOGIC TEMPLATE] spec. "
    "Your job is to write a SHORT, precise build plan (max 20 lines). "
    "If a template spec is provided: read it, note what to keep and what to customize. "
    "If no template: briefly outline the tech approach and component list. "
    "Do NOT write code. Do NOT pad with explanations. Be direct and specific."
)

BASE_ENGINEER = (
    "You are Byte the Builder — Senior Lead Developer for NymbleLogic. "
    "\n\nYour PRIMARY RULE: Output ONE complete, self-contained HTML file. "
    "ALL CSS inside <style>. ALL JS inside <script> at the bottom of <body>. "
    "NO external CDN links. NO imports. Inline EVERYTHING. "
    "Wrap your ENTIRE output in a SINGLE ```html ... ``` block — nothing before or after. "
    "\n\nCOMPLETENESS IS MANDATORY: "
    "- The file must be 100% complete. Never truncate or use '...' placeholders. "
    "- Every button must have a working onclick handler. "
    "- Every game must have full win/lose/draw detection and display. "
    "- Every UI element must render correctly on first load. "
    "- Test mentally: could a user open this file and immediately use it? If not, fix it. "
    "\n\nIF a [NYMBLELOGIC TEMPLATE] spec is present: "
    "1. Preserve all logic listed under DO NOT TOUCH. "
    "2. Only customize fields listed under SAFE TO CUSTOMIZE. "
    "3. Do NOT rewrite working mechanics — modify, not replace. "
    "\n\nIF no template spec: Build complete, polished single-file HTML from scratch. "
    "Use vanilla JS only. Make it fully functional — no placeholder UI, no empty states. "
    "\n\nQUALITY BAR: Immediately playable or usable. No broken buttons. No missing logic. No empty screens."
)

BASE_QA = (
    "You are Scout the Tester — QA engineer for NymbleLogic. "
    "Review the HTML/JS code from Byte the Builder. Be fast and ruthless. "
    "\n\nCheck for: "
    "1. Missing or broken win/lose/draw states in games. "
    "2. JavaScript errors that would crash or freeze the app. "
    "3. Buttons or interactions that have no handler or do nothing. "
    "4. Infinite loops or logic that would freeze the browser. "
    "5. Incomplete rendering — empty screens, missing UI on load. "
    "\n\nRespond in EXACTLY this format: "
    "VERDICT: PASS or FAIL "
    "CRITICAL BUGS: (numbered list, or NONE) "
    "FIXES: (for each bug, provide the EXACT replacement code snippet — no full rewrites unless <20 lines total) "
    "\n\nIf PASS: write 'VERDICT: PASS' and nothing else. Do not pad."
)

BASE_FIXER = (
    "You are Byte the Builder in FIX MODE. "
    "You are given: the original HTML app code AND a QA report listing critical bugs and fixes. "
    "\n\nYour job: Apply ONLY the listed fixes to the code. "
    "Do NOT rewrite the whole app. Do NOT change anything not listed in the fixes. "
    "Output the COMPLETE corrected HTML file in a single ```html ... ``` block. "
    "The file must be 100% complete — never truncate."
)


def build_agent_prompt(base: str, app_mode: str) -> str:
    prompt = base + SAFETY_GOVERNOR
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
    namespace: str = "nymblelogic"
    phase: str = ""
    write_memory: bool = False
    app_mode: str = "kid"


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
    fix_attempts: int = 0  # How many Scout fix loops ran


# ---------------------------------------------------------------------------
# Code Extractor
# ---------------------------------------------------------------------------
def extract_html(text: str) -> str:
    """Pull the first ```html ... ``` block. Falls back to raw text if none found."""
    match = re.search(r"```html\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: if the text starts with <!DOCTYPE or <html, use it directly
    stripped = text.strip()
    if stripped.lower().startswith("<!doctype") or stripped.lower().startswith("<html"):
        return stripped
    return text.strip()


def scout_passed(qa_response: str) -> bool:
    """Returns True if Scout gave a PASS verdict."""
    first_line = qa_response.strip().splitlines()[0] if qa_response.strip() else ""
    return "PASS" in first_line.upper() and "FAIL" not in first_line.upper()


# ---------------------------------------------------------------------------
# LLM Callers
# ---------------------------------------------------------------------------
async def call_claude(
    task: str, context: str, system_prompt: str, client: httpx.AsyncClient
) -> AgentResponse:
    try:
        messages = []
        if context:
            messages.append({"role": "user",      "content": f"[CONTEXT]\n{context}"})
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
        return AgentResponse(agent="Atlas (Architect)", response=r.json()["content"][0]["text"])
    except Exception as e:
        return AgentResponse(agent="Atlas (Architect)", response="", error=str(e))


async def call_gpt(
    task: str, context: str, system_prompt: str, client: httpx.AsyncClient,
    agent_label: str = "Byte (Builder)"
) -> AgentResponse:
    try:
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "user",      "content": f"[CONTEXT]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood. I have reviewed the context."})
        messages.append({"role": "user", "content": task})

        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",          # ← upgraded from gpt-4o-mini for quality
                "max_tokens": 8192,         # ← doubled to prevent truncation
                "messages": messages,
            },
            timeout=180,
        )
        r.raise_for_status()
        return AgentResponse(
            agent=agent_label,
            response=r.json()["choices"][0]["message"]["content"]
        )
    except Exception as e:
        return AgentResponse(agent=agent_label, response="", error=str(e))


async def call_gemini(
    task: str, context: str, system_prompt: str, client: httpx.AsyncClient
) -> AgentResponse:
    try:
        full_prompt = system_prompt + "\n\n"
        if context:
            full_prompt += f"[CONTEXT]\n{context}\n\n"
        full_prompt += task

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
        return AgentResponse(agent="Scout (QA Tester)", response=text)
    except Exception as e:
        return AgentResponse(agent="Scout (QA Tester)", response="", error=str(e))


# ---------------------------------------------------------------------------
# Scout Fix Loop
# ---------------------------------------------------------------------------
async def run_scout_fix_loop(
    task: str,
    initial_code: str,
    qa_report: str,
    app_mode: str,
    client: httpx.AsyncClient,
) -> tuple[str, str, int]:
    """
    If Scout gives a FAIL, feed the bugs + code back to GPT (as Fixer).
    Returns (final_code, final_qa_report, attempts_used).
    """
    code = initial_code
    qa   = qa_report
    attempts = 0

    for attempt in range(MAX_FIX_ATTEMPTS):
        if scout_passed(qa):
            break

        attempts += 1
        fixer_prompt = build_agent_prompt(BASE_FIXER, app_mode)
        fix_task = (
            f"Original request: {task}\n\n"
            f"QA REPORT:\n{qa}\n\n"
            f"CURRENT CODE:\n```html\n{code}\n```\n\n"
            "Apply the listed fixes and return the complete corrected HTML file."
        )

        fixed_res = await call_gpt(fix_task, "", fixer_prompt, client, agent_label="Byte (Fixer)")
        if fixed_res.error or not fixed_res.response:
            break  # Don't loop on API error

        fixed_code = extract_html(fixed_res.response)
        if not fixed_code:
            break

        # Re-run Scout on the fixed code
        qa_prompt = build_agent_prompt(BASE_QA, app_mode)
        re_qa = await call_gemini(
            f"Review this corrected code:\n```html\n{fixed_code}\n```",
            "",
            qa_prompt,
            client,
        )
        code = fixed_code
        qa   = re_qa.response if re_qa.response else qa

    return code, qa, attempts


# ---------------------------------------------------------------------------
# SSE Stage Events Helper
# ---------------------------------------------------------------------------
def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# Streaming Build Endpoint
# ---------------------------------------------------------------------------
@app.post("/consult/stream")
async def consult_stream(req: TaskRequest):
    """
    Server-Sent Events endpoint — pushes stage updates to the frontend
    so stage cards advance in real time instead of on a dumb timer.
    """
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    architect_prompt = build_agent_prompt(BASE_ARCHITECT, req.app_mode)
    engineer_prompt  = build_agent_prompt(BASE_ENGINEER,  req.app_mode)
    qa_prompt        = build_agent_prompt(BASE_QA,        req.app_mode)
    full_context     = req.context or ""

    async def event_stream():
        async with httpx.AsyncClient() as client:

            # ── Stage 1: Atlas ──────────────────────────────────────────
            yield sse_event("stage", {"stage": "atlas", "status": "active"})
            claude_res = await call_claude(req.task, full_context, architect_prompt, client)
            yield sse_event("stage", {"stage": "atlas", "status": "done"})
            yield sse_event("agent", {"agent": "atlas", "response": claude_res.response, "error": claude_res.error})

            # ── Stage 2: Byte ───────────────────────────────────────────
            yield sse_event("stage", {"stage": "byte", "status": "active"})
            engineer_context = full_context
            if claude_res.response:
                engineer_context += f"\n\n[ARCHITECT PLAN]\n{claude_res.response}"
            gpt_res = await call_gpt(req.task, engineer_context, engineer_prompt, client)
            raw_code = extract_html(gpt_res.response)
            yield sse_event("stage", {"stage": "byte", "status": "done"})
            yield sse_event("agent", {"agent": "byte", "response": gpt_res.response, "error": gpt_res.error})

            # ── Stage 3: Scout ──────────────────────────────────────────
            yield sse_event("stage", {"stage": "scout", "status": "active"})
            qa_context = engineer_context + (f"\n\n[ENGINEER CODE]\n{gpt_res.response}" if gpt_res.response else "")
            gemini_res = await call_gemini(req.task, qa_context, qa_prompt, client)
            yield sse_event("stage", {"stage": "scout", "status": "done"})
            yield sse_event("agent", {"agent": "scout", "response": gemini_res.response, "error": gemini_res.error})

            # ── Stage 4: Fix Loop (if Scout failed) ─────────────────────
            fix_attempts = 0
            final_code   = raw_code
            final_qa     = gemini_res.response

            if not scout_passed(gemini_res.response) and raw_code:
                yield sse_event("stage", {"stage": "shield", "status": "active"})
                yield sse_event("fix",   {"message": "Scout found bugs — Byte is patching…"})
                final_code, final_qa, fix_attempts = await run_scout_fix_loop(
                    req.task, raw_code, gemini_res.response, req.app_mode, client
                )
                yield sse_event("stage", {"stage": "shield", "status": "done"})
            else:
                yield sse_event("stage", {"stage": "shield", "status": "done"})

            # ── Stage 5: PM Synthesis ────────────────────────────────────
            results = [claude_res, gpt_res, gemini_res]
            try:
                consensus_data = await run_consensus_pipeline(
                    task=req.task,
                    claude_response=claude_res.response,
                    gpt_response=final_code,   # Send final (fixed) code to PM
                    gemini_response=final_qa,
                    client=client,
                    namespace=req.namespace,
                    phase=req.phase,
                    write_memory=req.write_memory,
                )
            except Exception as e:
                consensus_data = {
                    "raw": f"Synthesis error: {e}",
                    "summary": "", "disagreements": "",
                    "final_decision": "", "actionable_prompt": "",
                    "memory_items": [], "memory_writes": [],
                }

            # ── Final payload ─────────────────────────────────────────
            payload = {
                "results": [
                    {"agent": r.agent, "response": r.response, "error": r.error}
                    for r in results
                ],
                "final_code":       final_code,
                "consensus":        consensus_data["raw"],
                "summary":          consensus_data["summary"],
                "disagreements":    consensus_data["disagreements"],
                "final_decision":   consensus_data["final_decision"],
                "actionable_prompt":consensus_data["actionable_prompt"],
                "memory_items":     consensus_data["memory_items"],
                "memory_writes":    consensus_data["memory_writes"],
                "fix_attempts":     fix_attempts,
            }
            yield sse_event("complete", payload)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Non-streaming fallback (keeps backward compat)
# ---------------------------------------------------------------------------
@app.post("/consult", response_model=HouseResponse)
async def consult(req: TaskRequest):
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    architect_prompt = build_agent_prompt(BASE_ARCHITECT, req.app_mode)
    engineer_prompt  = build_agent_prompt(BASE_ENGINEER,  req.app_mode)
    qa_prompt        = build_agent_prompt(BASE_QA,        req.app_mode)
    full_context     = req.context or ""

    async with httpx.AsyncClient() as client:
        claude_res = await call_claude(req.task, full_context, architect_prompt, client)

        engineer_context = full_context
        if claude_res.response:
            engineer_context += f"\n\n[ARCHITECT PLAN]\n{claude_res.response}"
        gpt_res = await call_gpt(req.task, engineer_context, engineer_prompt, client)

        qa_context = engineer_context + (f"\n\n[ENGINEER CODE]\n{gpt_res.response}" if gpt_res.response else "")
        gemini_res = await call_gemini(req.task, qa_context, qa_prompt, client)

        raw_code     = extract_html(gpt_res.response)
        final_code   = raw_code
        final_qa     = gemini_res.response
        fix_attempts = 0

        if not scout_passed(gemini_res.response) and raw_code:
            final_code, final_qa, fix_attempts = await run_scout_fix_loop(
                req.task, raw_code, gemini_res.response, req.app_mode, client
            )

        results = [claude_res, gpt_res, gemini_res]

        try:
            consensus_data = await run_consensus_pipeline(
                task=req.task,
                claude_response=claude_res.response,
                gpt_response=final_code,
                gemini_response=final_qa,
                client=client,
                namespace=req.namespace,
                phase=req.phase,
                write_memory=req.write_memory,
            )
        except Exception as e:
            consensus_data = {
                "raw": f"Synthesis error: {e}",
                "summary": "", "disagreements": "",
                "final_decision": "", "actionable_prompt": "",
                "memory_items": [], "memory_writes": [],
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
        fix_attempts=fix_attempts,
    )


# ---------------------------------------------------------------------------
# TTS — Extended for Kid Mode
# ---------------------------------------------------------------------------
KID_VOICES = ["nova", "shimmer"]   # Warmer voices for kids
PRO_VOICES = ["onyx", "echo"]

class TTSRequest(BaseModel):
    text: str
    voice: str = ""
    app_mode: str = "kid"

class SimpleQueryRequest(BaseModel):
    prompt: str

class SimpleQueryResponse(BaseModel):
    prompt: str
    responses: dict

@app.post("/ask", response_model=SimpleQueryResponse)
async def ask_all_ais(req: SimpleQueryRequest):
    """
    Simple multi-AI query - ask one question, get individual responses from each AI
    exactly like going to each website separately
    """
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    responses = {}
    simple_system_prompt = "You are a helpful AI assistant. Answer the user's question directly and naturally."

    async with httpx.AsyncClient() as client:
        # Query Claude (Anthropic)
        if ANTHROPIC_API_KEY:
            try:
                claude_result = await call_claude(req.prompt, "", simple_system_prompt, client)
                responses["claude"] = claude_result.response if not claude_result.error else f"Error: {claude_result.error}"
            except Exception as e:
                responses["claude"] = f"Error: {str(e)}"
        else:
            responses["claude"] = "No API key configured"

        # Query GPT (OpenAI)
        if OPENAI_API_KEY:
            try:
                gpt_result = await call_gpt(req.prompt, "", simple_system_prompt, client, "GPT")
                responses["gpt"] = gpt_result.response if not gpt_result.error else f"Error: {gpt_result.error}"
            except Exception as e:
                responses["gpt"] = f"Error: {str(e)}"
        else:
            responses["gpt"] = "No API key configured"

        # Query Gemini (Google)
        if GEMINI_API_KEY:
            try:
                gemini_result = await call_gemini(req.prompt, "", simple_system_prompt, client)
                responses["gemini"] = gemini_result.response if not gemini_result.error else f"Error: {gemini_result.error}"
            except Exception as e:
                responses["gemini"] = f"Error: {str(e)}"
        else:
            responses["gemini"] = "No API key configured"

    return SimpleQueryResponse(prompt=req.prompt, responses=responses)

@app.post("/tts")
async def tts_endpoint(req: TTSRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="TTS not configured.")
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text required.")

    text = text[:600]  # Raised cap from 300 → 600 chars

    # Auto-select voice if not specified
    voice = req.voice
    if not voice:
        voice = KID_VOICES[0] if req.app_mode == "kid" else PRO_VOICES[0]

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": "tts-1", "input": text, "voice": voice},
                timeout=30,
            )
            r.raise_for_status()
            from fastapi.responses import Response
            return Response(content=r.content, media_type="audio/mpeg")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"TTS error: {e}")


# ---------------------------------------------------------------------------
# Health + Static
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "status": "NymbleLogic — House of AI live",
        "safety_layer": "active",
        "fix_loop": f"max {MAX_FIX_ATTEMPTS} attempts",
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")
