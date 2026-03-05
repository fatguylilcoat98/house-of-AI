"""
main.py — House of AI (Upgraded)
The Good Neighbor Guard — Veracore Coordination Layer

Upgrade: turns "3 panels + Claude summary" into a real orchestration response:
- persistent http client (startup/shutdown)
- key validation at startup
- hardened parsing for Claude/OpenAI/Gemini
- timeouts + non-blocking gather
- consensus skips failed agents
- adds: consensus_score, conflicts, action_items, confidence_estimate
- adds: per-agent latency + status
"""

import os
import time
import asyncio
import httpx
from typing import Optional, List, Dict, Any, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = FastAPI(title="House of AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Config — set these as Render environment variables
# -----------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Use models you actually want here
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-5").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

REQUEST_TIMEOUT_SECS = float(os.getenv("REQUEST_TIMEOUT_SECS", "60"))

SYSTEM_PROMPT = (
    "You are a senior AI engineer on the Veracore fact-verification engine "
    "project for The Good Neighbor Guard. You are collaborating with two other "
    "AI systems. Give your honest technical assessment. Be direct. "
    "Flag disagreements. Do not pad your response."
)

# -----------------------------------------------------------------------------
# Global HTTP client (created at startup)
# -----------------------------------------------------------------------------
_http: Optional[httpx.AsyncClient] = None


@app.on_event("startup")
async def _startup():
    global _http

    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")

    if missing:
        # crash early so Render logs show the real reason
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    _http = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECS)


@app.on_event("shutdown")
async def _shutdown():
    global _http
    if _http:
        await _http.aclose()
        _http = None


def _client() -> httpx.AsyncClient:
    if _http is None:
        # Should never happen if startup succeeded
        raise RuntimeError("HTTP client not initialized")
    return _http


# -----------------------------------------------------------------------------
# Request / Response models
# -----------------------------------------------------------------------------
class TaskRequest(BaseModel):
    task: str
    context: str = ""  # optional: paste prior phase output here


class AgentResponse(BaseModel):
    agent: str
    response: str = ""
    error: str = ""
    status: str = "ok"  # ok | error
    latency_ms: int = 0


class OrchestratedConsensus(BaseModel):
    consensus: str
    consensus_score: int  # 0-100
    confidence_estimate: str  # LOW | MODERATE | HIGH
    agreements: List[str]
    conflicts: List[str]
    action_items: List[str]


class HouseResponse(BaseModel):
    results: List[AgentResponse]
    orchestrator: OrchestratedConsensus


# -----------------------------------------------------------------------------
# Helpers: robust parsing
# -----------------------------------------------------------------------------
def _safe_json(r: httpx.Response) -> Dict[str, Any]:
    try:
        return r.json()
    except Exception:
        # preserve first chunk for debugging
        preview = (r.text or "")[:400]
        raise RuntimeError(f"Non-JSON response ({r.status_code}): {preview!r}")


def _parse_claude_text(data: Dict[str, Any]) -> str:
    # Anthropic returns content blocks; gather all text blocks
    blocks = data.get("content", []) or []
    out = []
    for b in blocks:
        if isinstance(b, dict) and b.get("type") == "text":
            out.append(b.get("text", ""))
        # if it's already the older format or weird, try best-effort
        elif isinstance(b, dict) and "text" in b:
            out.append(b.get("text", ""))
    return "".join(out).strip()


def _parse_openai_text(data: Dict[str, Any]) -> str:
    # Chat Completions style
    try:
        return (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
    except Exception:
        return ""


def _parse_gemini_text(data: Dict[str, Any]) -> str:
    # Gemini candidate parts can vary
    cand = (data.get("candidates") or [{}])[0] or {}
    content = cand.get("content") or {}
    parts = content.get("parts") or []
    out = []
    for p in parts:
        if isinstance(p, dict) and "text" in p:
            out.append(p.get("text", ""))
    return "".join(out).strip()


def _clamp_0_100(n: int) -> int:
    if n < 0:
        return 0
    if n > 100:
        return 100
    return n


# -----------------------------------------------------------------------------
# LLM Callers
# -----------------------------------------------------------------------------
async def call_claude(task: str, context: str) -> AgentResponse:
    t0 = time.perf_counter()
    try:
        messages = []
        if context:
            messages.append({"role": "user", "content": f"[CONTEXT FROM PRIOR PHASE]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood. I have the context."})
        messages.append({"role": "user", "content": task})

        r = await _client().post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 2048,
                "system": SYSTEM_PROMPT,
                "messages": messages,
            },
        )
        r.raise_for_status()
        data = _safe_json(r)
        text = _parse_claude_text(data)
        return AgentResponse(agent="Claude", response=text, status="ok", latency_ms=int((time.perf_counter() - t0) * 1000))
    except Exception as e:
        return AgentResponse(agent="Claude", error=str(e), status="error", latency_ms=int((time.perf_counter() - t0) * 1000))


async def call_gpt(task: str, context: str) -> AgentResponse:
    t0 = time.perf_counter()
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "user", "content": f"[CONTEXT FROM PRIOR PHASE]\n{context}"})
            messages.append({"role": "assistant", "content": "Understood. I have the context."})
        messages.append({"role": "user", "content": task})

        r = await _client().post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "max_tokens": 2048,
                "messages": messages,
            },
        )
        r.raise_for_status()
        data = _safe_json(r)
        text = _parse_openai_text(data)
        return AgentResponse(agent="GPT", response=text, status="ok", latency_ms=int((time.perf_counter() - t0) * 1000))
    except Exception as e:
        return AgentResponse(agent="GPT", error=str(e), status="error", latency_ms=int((time.perf_counter() - t0) * 1000))


async def call_gemini(task: str, context: str) -> AgentResponse:
    t0 = time.perf_counter()
    try:
        full_prompt = SYSTEM_PROMPT + "\n\n"
        if context:
            full_prompt += f"[CONTEXT FROM PRIOR PHASE]\n{context}\n\n"
        full_prompt += task

        r = await _client().post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"maxOutputTokens": 2048},
            },
        )
        r.raise_for_status()
        data = _safe_json(r)
        text = _parse_gemini_text(data)
        return AgentResponse(agent="Gemini", response=text, status="ok", latency_ms=int((time.perf_counter() - t0) * 1000))
    except Exception as e:
        return AgentResponse(agent="Gemini", error=str(e), status="error", latency_ms=int((time.perf_counter() - t0) * 1000))


# -----------------------------------------------------------------------------
# Orchestrator: true "council" output (structured, scored)
# -----------------------------------------------------------------------------
async def build_orchestrator(results: List[AgentResponse], task: str) -> OrchestratedConsensus:
    """
    Uses Claude as a coordinator, but:
    - filters out failed agents
    - forces strict JSON output
    - extracts agreements/conflicts/action items
    """
    valid = [r for r in results if r.status == "ok" and r.response.strip()]
    failed = [r for r in results if r.status != "ok"]

    if not valid:
        return OrchestratedConsensus(
            consensus="All agents failed. Check API keys, model names, and provider status.",
            consensus_score=0,
            confidence_estimate="LOW",
            agreements=[],
            conflicts=[f"{r.agent}: {r.error}" for r in failed],
            action_items=["Fix provider errors and retry."],
        )

    summaries = "\n\n".join(
        f"=== {r.agent} (latency {r.latency_ms}ms) ===\n{r.response}" for r in valid
    )
    if failed:
        summaries += "\n\n" + "\n".join(f"=== {r.agent} FAILED ===\n{r.error}" for r in failed)

    meta_prompt = (
        "You are the ORCHESTRATOR.\n"
        "Return STRICT JSON ONLY (no markdown, no prose outside JSON).\n\n"
        "Schema:\n"
        "{\n"
        '  "consensus": "string",\n'
        '  "consensus_score": 0-100 integer,\n'
        '  "confidence_estimate": "LOW"|"MODERATE"|"HIGH",\n'
        '  "agreements": ["..."],\n'
        '  "conflicts": ["..."],\n'
        '  "action_items": ["..."]\n'
        "}\n\n"
        f"ORIGINAL TASK:\n{task}\n\n"
        f"AGENT RESPONSES:\n{summaries}\n\n"
        "Rules:\n"
        "- Be blunt.\n"
        "- If agents disagree, list the exact conflict.\n"
        "- If sources/claims are missing, include an action item: 'Ask for sources / run retrieval'.\n"
    )

    # call Claude again as orchestrator
    t0 = time.perf_counter()
    try:
        r = await _client().post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 600,
                "system": "You are a technical coordinator. Output STRICT JSON only.",
                "messages": [{"role": "user", "content": meta_prompt}],
            },
        )
        r.raise_for_status()
        data = _safe_json(r)
        txt = _parse_claude_text(data)

        # Strict JSON parse
        try:
            obj = __import__("json").loads(txt)
        except Exception:
            # hard fallback: wrap raw text
            return OrchestratedConsensus(
                consensus=f"Orchestrator returned non-JSON. Raw:\n{txt}",
                consensus_score=20,
                confidence_estimate="LOW",
                agreements=[],
                conflicts=["Orchestrator formatting error (non-JSON)."],
                action_items=["Fix orchestrator prompt/format; retry."],
            )

        return OrchestratedConsensus(
            consensus=str(obj.get("consensus", "")).strip(),
            consensus_score=_clamp_0_100(int(obj.get("consensus_score", 0))),
            confidence_estimate=str(obj.get("confidence_estimate", "LOW")).strip().upper(),
            agreements=list(obj.get("agreements", [])) if isinstance(obj.get("agreements", []), list) else [],
            conflicts=list(obj.get("conflicts", [])) if isinstance(obj.get("conflicts", []), list) else [],
            action_items=list(obj.get("action_items", [])) if isinstance(obj.get("action_items", []), list) else [],
        )
    except Exception as e:
        return OrchestratedConsensus(
            consensus=f"Consensus engine error: {e}",
            consensus_score=10,
            confidence_estimate="LOW",
            agreements=[],
            conflicts=[str(e)],
            action_items=["Fix consensus provider error and retry."],
        )
    finally:
        _ = int((time.perf_counter() - t0) * 1000)


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.post("/consult", response_model=HouseResponse)
async def consult(req: TaskRequest):
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    # Parallel fan-out, non-blocking failures
    calls = await asyncio.gather(
        call_claude(req.task, req.context),
        call_gpt(req.task, req.context),
        call_gemini(req.task, req.context),
        return_exceptions=True,
    )

    results: List[AgentResponse] = []
    for c in calls:
        if isinstance(c, Exception):
            results.append(AgentResponse(agent="Unknown", error=str(c), status="error"))
        else:
            results.append(c)

    # stable ordering for UI
    order = {"Claude": 0, "GPT": 1, "Gemini": 2}
    results.sort(key=lambda r: order.get(r.agent, 99))

    orchestrator = await build_orchestrator(results, req.task)
    return HouseResponse(results=results, orchestrator=orchestrator)


@app.get("/health")
async def health():
    return {"status": "House is live"}


# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")