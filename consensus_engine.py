"""
consensus_engine.py
The Good Neighbor Guard — House of AI
Compresses Claude + GPT + Gemini responses into one actionable output.
Optionally writes key decisions to Pinecone memory.
"""

import os
import re
import httpx
from typing import Optional
from memory_engine import memory_write

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

CONSENSUS_SYSTEM = """You are the Consensus Synthesizer for the House of AI — a coordination layer
for the Veracore fact-verification engine (The Good Neighbor Guard).

You receive responses from three AI engineers (Claude, GPT, Gemini) on a technical task.
Your job is to compress them into one structured output.

Respond in EXACTLY this format — no deviations:

CONSENSUS SUMMARY
• [bullet]
• [bullet]
• [bullet]
(3–5 bullets max — agreements only)

DISAGREEMENTS
• [bullet or "None detected"]

FINAL DECISION
[One short paragraph. What is the correct path forward? Be direct.]

ACTIONABLE PROMPT
[A ready-to-copy prompt addressed to Claude for implementation.
Must be concise, contain only necessary context, no fluff.
Start with: CLAUDE — ]

MEMORY ITEMS
[List 1–3 short facts worth storing. One per line, prefixed with "- ".
These must be objective facts about the project state, not opinions.
Example: - Phase 5 deterministic engine complete]"""


async def generate_consensus(
    task: str,
    claude_response: str,
    gpt_response: str,
    gemini_response: str,
    client: httpx.AsyncClient,
) -> str:
    """
    Call Claude to synthesize three responses into structured consensus output.
    Returns the raw structured text.
    """
    combined = (
        f"ORIGINAL TASK:\n{task}\n\n"
        f"=== CLAUDE ===\n{claude_response or '[no response]'}\n\n"
        f"=== GPT ===\n{gpt_response or '[no response]'}\n\n"
        f"=== GEMINI ===\n{gemini_response or '[no response]'}"
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
            "system": CONSENSUS_SYSTEM,
            "messages": [{"role": "user", "content": combined}],
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def parse_consensus(raw: str) -> dict:
    """
    Parse the structured consensus text into a dict with sections:
    summary, disagreements, final_decision, actionable_prompt, memory_items
    """
    sections = {
        "summary":          "",
        "disagreements":    "",
        "final_decision":   "",
        "actionable_prompt": "",
        "memory_items":     [],
    }

    # Split on known section headers
    pattern = re.compile(
        r"(CONSENSUS SUMMARY|DISAGREEMENTS|FINAL DECISION|ACTIONABLE PROMPT|MEMORY ITEMS)",
        re.IGNORECASE,
    )
    parts = pattern.split(raw)

    current = None
    for part in parts:
        key = part.strip().upper()
        if key == "CONSENSUS SUMMARY":
            current = "summary"
        elif key == "DISAGREEMENTS":
            current = "disagreements"
        elif key == "FINAL DECISION":
            current = "final_decision"
        elif key == "ACTIONABLE PROMPT":
            current = "actionable_prompt"
        elif key == "MEMORY ITEMS":
            current = "memory_items"
        elif current:
            cleaned = part.strip()
            if current == "memory_items":
                items = [
                    line.lstrip("- •").strip()
                    for line in cleaned.splitlines()
                    if line.strip() and line.strip() not in ("", "None")
                ]
                sections["memory_items"] = items
            else:
                sections[current] = cleaned

    return sections


async def store_memory(
    parsed: dict,
    task: str,
    namespace: str = "veracore",
    phase: str = "",
) -> list[dict]:
    """
    Write memory_items from parsed consensus to Pinecone.
    Returns list of write results.
    """
    results = []
    for item in parsed.get("memory_items", []):
        if not item:
            continue
        result = await memory_write({
            "text":      item,
            "project":   namespace,
            "type":      "architecture_decision",
            "phase":     phase,
            "tags":      ["consensus", "auto"],
            "confidence": 0.9,
        })
        results.append(result)
    return results


async def run_consensus_pipeline(
    task: str,
    claude_response: str,
    gpt_response: str,
    gemini_response: str,
    client: httpx.AsyncClient,
    namespace: str = "veracore",
    phase: str = "",
    write_memory: bool = True,
) -> dict:
    """
    Full pipeline:
    1. Generate consensus
    2. Parse into sections
    3. Optionally write memory items to Pinecone
    4. Return full structured result
    """
    raw = await generate_consensus(
        task, claude_response, gpt_response, gemini_response, client
    )
    parsed = parse_consensus(raw)

    memory_results = []
    if write_memory and parsed.get("memory_items"):
        memory_results = await store_memory(parsed, task, namespace, phase)

    return {
        "raw":              raw,
        "summary":          parsed["summary"],
        "disagreements":    parsed["disagreements"],
        "final_decision":   parsed["final_decision"],
        "actionable_prompt": parsed["actionable_prompt"],
        "memory_items":     parsed["memory_items"],
        "memory_writes":    memory_results,
    }
