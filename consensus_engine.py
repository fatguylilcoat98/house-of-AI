"""
consensus_engine.py
House of AI — Project Manager Synthesizer
Built by Christopher Hughes & The Good Neighbor Guard

Packages Architect + Engineer + QA Tester responses into one actionable output.
Memory writes are optional — stubs gracefully if Pinecone/memory_engine is unavailable.
"""

import os
import re
import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ---------------------------------------------------------------------------
# Memory Engine — Safe Stub
# If you have a real memory_engine.py, replace this with:
#   from memory_engine import memory_write
# The stub below ensures the server never crashes when memory is unavailable.
# ---------------------------------------------------------------------------
async def _memory_write_stub(payload: dict) -> dict:
    """No-op stub. Replace with real memory_write when Pinecone is connected."""
    return {"status": "stub", "payload": payload}

try:
    from memory_engine import memory_write  # type: ignore
except ImportError:
    memory_write = _memory_write_stub


# ---------------------------------------------------------------------------
# Project Manager System Prompt
# ---------------------------------------------------------------------------
PM_SYSTEM = """You are the Project Manager for the House of AI — a multi-agent coding council.

You receive outputs from three AI agents working on a user's app request:
1. The Architect (Claude): Structural design and tech stack.
2. The Senior Engineer (GPT): Raw code execution.
3. The QA Tester (Gemini): Security and bug review.

Your job is to compress their work into one structured, actionable output.

Respond in EXACTLY this format — no deviations, no extra headers:

ARCHITECTURE SUMMARY
• [bullet - key tech stack choices]
• [bullet - major structural decisions]

QA REVIEW & RISKS
• [bullet - critical bugs found, or 'None found']
• [bullet - security vulnerabilities, or 'None detected']

FINAL CODE STATUS
[One short paragraph. Is the code ready to deploy, or does it need manual fixes?]

ACTIONABLE NEXT STEP
[A concise next step for the developer. What should they do right now?]

MEMORY ITEMS
[List 1–3 short objective facts worth storing about this project. One per line, prefixed with "- ".
Example: - App uses a single-file HTML architecture with inline CSS and JS.]"""


# ---------------------------------------------------------------------------
# Consensus Generator
# ---------------------------------------------------------------------------
async def generate_consensus(
    task: str,
    claude_response: str,
    gpt_response: str,
    gemini_response: str,
    client: httpx.AsyncClient,
) -> str:
    """
    Call Claude (Synthesizer) to package the three agent outputs into
    a structured Project Manager report. Returns raw structured text.
    """
    combined = (
        f"ORIGINAL USER PROMPT:\n{task}\n\n"
        f"=== ARCHITECT (CLAUDE) ===\n{claude_response or '[no response received]'}\n\n"
        f"=== SENIOR ENGINEER (GPT) ===\n{gpt_response or '[no response received]'}\n\n"
        f"=== QA TESTER (GEMINI) ===\n{gemini_response or '[no response received]'}"
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
            "max_tokens": 1024,
            "system": PM_SYSTEM,
            "messages": [{"role": "user", "content": combined}],
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]


# ---------------------------------------------------------------------------
# Consensus Parser
# ---------------------------------------------------------------------------
def parse_consensus(raw: str) -> dict:
    """
    Parse the structured PM text into a dict with named sections.
    Handles minor formatting variations from the LLM gracefully.
    """
    sections = {
        "summary":           "",
        "disagreements":     "",  # Maps to "QA REVIEW & RISKS" — kept for API compat
        "final_decision":    "",
        "actionable_prompt": "",
        "memory_items":      [],
    }

    # Split on the known section headers
    pattern = re.compile(
        r"(ARCHITECTURE SUMMARY|QA REVIEW & RISKS|FINAL CODE STATUS|ACTIONABLE NEXT STEP|MEMORY ITEMS)",
        re.IGNORECASE,
    )
    parts = pattern.split(raw)

    current = None
    for part in parts:
        key = part.strip().upper()
        if key == "ARCHITECTURE SUMMARY":
            current = "summary"
        elif key == "QA REVIEW & RISKS":
            current = "disagreements"
        elif key == "FINAL CODE STATUS":
            current = "final_decision"
        elif key == "ACTIONABLE NEXT STEP":
            current = "actionable_prompt"
        elif key == "MEMORY ITEMS":
            current = "memory_items"
        elif current:
            cleaned = part.strip()
            if current == "memory_items":
                items = [
                    line.lstrip("-• ").strip()
                    for line in cleaned.splitlines()
                    if line.strip() and line.strip() not in ("", "None")
                ]
                sections["memory_items"] = items
            else:
                sections[current] = cleaned

    return sections


# ---------------------------------------------------------------------------
# Memory Store
# ---------------------------------------------------------------------------
async def store_memory(
    parsed: dict,
    task: str,
    namespace: str = "house_of_ai",
    phase: str = "",
) -> list[dict]:
    """
    Write memory_items from parsed consensus to Pinecone.
    Returns list of write results. Silently skips on error.
    """
    results = []
    for item in parsed.get("memory_items", []):
        if not item:
            continue
        try:
            result = await memory_write({
                "text":       item,
                "project":    namespace,
                "type":       "architecture_decision",
                "phase":      phase,
                "tags":       ["house_of_ai", "auto_architecture"],
                "confidence": 0.9,
            })
            results.append(result)
        except Exception as e:
            results.append({"status": "error", "error": str(e)})
    return results


# ---------------------------------------------------------------------------
# Full Pipeline Entry Point
# ---------------------------------------------------------------------------
async def run_consensus_pipeline(
    task: str,
    claude_response: str,
    gpt_response: str,
    gemini_response: str,
    client: httpx.AsyncClient,
    namespace: str = "house_of_ai",
    phase: str = "",
    write_memory: bool = False,
) -> dict:
    """
    Full pipeline:
    1. Generate PM synthesis via Claude
    2. Parse into named sections
    3. Optionally write memory items to Pinecone
    4. Return full structured result dict
    """
    raw = await generate_consensus(
        task, claude_response, gpt_response, gemini_response, client
    )
    parsed = parse_consensus(raw)

    memory_results = []
    if write_memory and parsed.get("memory_items"):
        memory_results = await store_memory(parsed, task, namespace, phase)

    return {
        "raw":               raw,
        "summary":           parsed["summary"],
        "disagreements":     parsed["disagreements"],
        "final_decision":    parsed["final_decision"],
        "actionable_prompt": parsed["actionable_prompt"],
        "memory_items":      parsed["memory_items"],
        "memory_writes":     memory_results,
    }
