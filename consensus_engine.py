"""
consensus_engine.py
House of AI — Project Manager Synthesizer
Packages Architect + Engineer + QA Tester responses into one actionable output.
Optionally writes key decisions to Pinecone memory.
"""

import os
import re
import httpx
from typing import Optional
from memory_engine import memory_write

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

PM_SYSTEM = """You are the Project Manager for the House of AI — a multi-agent coding council.

You receive responses from three AI agents on a user's app request:
1. The Architect (Claude): The structural design and tech stack.
2. The Senior Engineer (GPT): The raw code execution.
3. The QA Tester (Gemini): The security and bug review.

Your job is to compress their work into one structured, actionable output for the human developer.

Respond in EXACTLY this format — no deviations:

ARCHITECTURE SUMMARY
• [bullet - key tech stack choices]
• [bullet - major structural decisions]

QA REVIEW & RISKS
• [bullet - critical bugs or 'All clear' if QA passed]
• [bullet - security vulnerabilities or 'None detected']

FINAL CODE STATUS
[One short paragraph. Is the code ready to copy-paste and deploy, or does it require manual fixes based on the QA review?]

ACTIONABLE NEXT STEP
[A concise next step for the human developer. What should they do right now to move this forward?]

MEMORY ITEMS
[List 1–3 short facts worth storing about this project. One per line, prefixed with "- ".
These must be objective facts about the project state.
Example: - App architecture uses React, Node, and Supabase.]"""


async def generate_consensus(
    task: str,
    claude_response: str,
    gpt_response: str,
    gemini_response: str,
    client: httpx.AsyncClient,
) -> str:
    """
    Call Claude to synthesize the Developer Council responses into structured output.
    Returns the raw structured text.
    """
    combined = (
        f"ORIGINAL USER PROMPT:\n{task}\n\n"
        f"=== ARCHITECT (CLAUDE) ===\n{claude_response or '[no response]'}\n\n"
        f"=== SENIOR ENGINEER (GPT) ===\n{gpt_response or '[no response]'}\n\n"
        f"=== QA TESTER (GEMINI) ===\n{gemini_response or '[no response]'}"
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


def parse_consensus(raw: str) -> dict:
    """
    Parse the structured project manager text into a dict with sections.
    """
    sections = {
        "summary":          "",
        "disagreements":    "", # Kept for API model compatibility
        "final_decision":   "",
        "actionable_prompt": "",
        "memory_items":     [],
    }

    # Split on known section headers
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
            current = "disagreements" # Maps to the existing API model field
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
    namespace: str = "house_of_ai",
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
            "tags":      ["house_of_ai", "auto_architecture"],
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
    namespace: str = "house_of_ai",
    phase: str = "",
    write_memory: bool = True,
) -> dict:
    """
    Full pipeline:
    1. Generate project manager synthesis
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
