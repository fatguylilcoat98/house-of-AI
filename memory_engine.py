"""
memory_engine.py
The Good Neighbor Guard — House of AI
Pinecone-based persistent memory for Veracore coordination.

DO NOT store: API keys, system prompts, routing rules, secrets.
"""

import os
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional

from pinecone import Pinecone
import httpx

PINECONE_API_KEY   = os.getenv("PINECONE_API_KEY", "")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
PINECONE_INDEX     = "house-ai-memory"
EMBEDDING_MODEL    = "text-embedding-3-small"
TOP_K              = 5

VALID_NAMESPACES   = {"veracore", "lylo", "general"}
VALID_TYPES        = {
    "phase_spec", "architecture_decision", "bug",
    "patch", "test_result", "task"
}

# ---------------------------------------------------------------------------
# Pinecone client — lazy init
# ---------------------------------------------------------------------------
_pc_index = None

def _get_index():
    global _pc_index
    if _pc_index is None:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        _pc_index = pc.Index(PINECONE_INDEX)
    return _pc_index


# ---------------------------------------------------------------------------
# Embedding via OpenAI
# ---------------------------------------------------------------------------
async def _embed(text: str) -> list[float]:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": EMBEDDING_MODEL, "input": text},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def memory_write(event: dict) -> dict:
    """
    Write a memory event to Pinecone.

    Required fields:
        text      — the content to store and embed
        project   — namespace: veracore | lylo | general
        type      — memory type (phase_spec, bug, patch, etc.)

    Optional fields:
        phase       — e.g. "6"
        tags        — list of strings
        confidence  — float 0.0–1.0
    """
    text      = event.get("text", "").strip()
    project   = event.get("project", "general").lower()
    mem_type  = event.get("type", "task")
    phase     = str(event.get("phase", ""))
    tags      = event.get("tags", [])
    confidence = float(event.get("confidence", 1.0))

    if not text:
        return {"ok": False, "error": "text is required"}
    if project not in VALID_NAMESPACES:
        project = "general"
    if mem_type not in VALID_TYPES:
        mem_type = "task"

    # Safety check — never store secrets
    lowered = text.lower()
    blocked = ["api_key", "api key", "secret", "password", "token", "system prompt"]
    if any(b in lowered for b in blocked):
        return {"ok": False, "error": "Blocked: potential secret detected in text"}

    mem_id  = str(uuid.uuid4())
    vector  = await _embed(text)
    metadata = {
        "text":       text,
        "project":    project,
        "type":       mem_type,
        "phase":      phase,
        "tags":       tags,
        "confidence": confidence,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }

    def _upsert():
        idx = _get_index()
        idx.upsert(
            vectors=[{"id": mem_id, "values": vector, "metadata": metadata}],
            namespace=project,
        )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _upsert)

    return {"ok": True, "id": mem_id, "namespace": project}


async def memory_search(query: str, namespace: str = "veracore") -> list[dict]:
    """
    Search Pinecone for the top-K most relevant memories.
    Returns a list of metadata dicts.
    """
    if namespace not in VALID_NAMESPACES:
        namespace = "general"

    vector = await _embed(query)

    def _query():
        idx = _get_index()
        return idx.query(
            vector=vector,
            top_k=TOP_K,
            namespace=namespace,
            include_metadata=True,
        )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _query)

    memories = []
    for match in result.get("matches", []):
        meta = match.get("metadata", {})
        meta["score"] = round(match.get("score", 0.0), 4)
        memories.append(meta)

    return memories


async def memory_pack_for_prompt(query: str, namespace: str = "veracore") -> str:
    """
    Retrieve relevant memories and pack them into a
    formatted context block ready for injection into a prompt.
    """
    memories = await memory_search(query, namespace)
    if not memories:
        return ""

    lines = ["[PROJECT MEMORY]"]
    for i, m in enumerate(memories, 1):
        ts    = m.get("timestamp", "")[:10]
        mtype = m.get("type", "")
        phase = m.get("phase", "")
        text  = m.get("text", "")
        score = m.get("score", 0)
        phase_str = f" | Phase {phase}" if phase else ""
        lines.append(f"{i}. [{mtype}{phase_str}] ({ts}) [score:{score}]\n   {text}")

    return "\n".join(lines)
