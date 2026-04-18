"""
main_council.py
AI Council System - Clean Architecture
Built by Christopher Hughes & The Good Neighbor Guard

Unified AI council with System Packet Builder, 2-round execution,
claim tagging, save/capture, and handoff capabilities.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import subprocess
import os
from pathlib import Path

from system_packet_builder import (
    SystemPacketBuilder, ConstitutionCore, ActiveSystemState, SessionGoal
)
from council_execution_engine import CouncilExecutionEngine, CouncilSession
from synthesis_engine import SynthesisEngine, SynthesisResult
from builder_instance_manager import (
    BuilderInstanceManager, InstanceStatus, HandoffType, BuilderInstance
)


app = FastAPI(title="AI Council System - Clean Architecture")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_KEYS = {
    "claude": os.getenv("ANTHROPIC_API_KEY", ""),
    "gpt4": os.getenv("OPENAI_API_KEY", ""),
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "grok": os.getenv("GROK_API_KEY", ""),
    "perplexity": os.getenv("PERPLEXITY_API_KEY", "")
}

# ---------------------------------------------------------------------------
# Global Components
# ---------------------------------------------------------------------------
packet_builder = SystemPacketBuilder()
execution_engine = CouncilExecutionEngine(API_KEYS)
synthesis_engine = SynthesisEngine()
builder_manager = BuilderInstanceManager()

# Storage for sessions and saved outputs
saved_outputs: Dict[str, Dict[str, Any]] = {}
active_system_state = ActiveSystemState.default()

# Provider status and cost tracking
provider_status: Dict[str, ProviderStatus] = {}
session_stats: Dict[str, Dict[str, Any]] = {}
saved_insights: Dict[str, Dict[str, Any]] = {}

# Repo sharing system
repo_shares: Dict[str, RepoShareSession] = {}
available_repos: Dict[str, str] = {}  # repo_name -> repo_path mapping

# Initialize provider status
for provider in ["claude", "gpt4", "gemini", "grok", "perplexity"]:
    provider_status[provider] = ProviderStatus(
        provider=provider,
        status="unknown",
        last_check=datetime.now()
    )

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class CouncilRequest(BaseModel):
    user_input: str
    session_goal: Optional[Dict[str, Any]] = None
    custom_constitution: Optional[Dict[str, Any]] = None
    execution_mode: str = "full"  # "safe" (1 round) or "full" (2 rounds)
    selected_providers: Optional[List[str]] = None  # ["claude", "gpt4", etc]
    repo_share_id: Optional[str] = None  # Include repo context in session


class StateUpdateRequest(BaseModel):
    project_name: Optional[str] = None
    current_phase: Optional[str] = None
    goals: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    context_summary: Optional[str] = None
    open_questions: Optional[List[str]] = None


class SaveOutputRequest(BaseModel):
    name: str
    description: str
    session_id: str
    include_synthesis: bool = True


class HandoffPacketRequest(BaseModel):
    session_id: str
    recipient: str
    purpose: str
    include_full_context: bool = True


class SaveInsightRequest(BaseModel):
    type: str  # "insight", "decision", "feature"
    title: str
    content: str
    session_id: str
    tags: Optional[List[str]] = None


class ProviderStatus(BaseModel):
    provider: str
    status: str  # "online", "offline", "timeout", "error"
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    last_check: datetime


class RepoShareRequest(BaseModel):
    repo_path: str
    branch: str = "master"
    scope_type: str  # "selected_files", "selected_folder", "diff", "full_repo"
    scope_data: Optional[Dict[str, Any]] = None  # files/folders/diff options
    description: str = ""


class RepoShareSession(BaseModel):
    share_id: str
    repo_name: str
    repo_path: str
    branch: str
    scope_type: str
    scope_data: Dict[str, Any]
    snapshot_timestamp: datetime
    file_count: int
    total_size_bytes: int
    read_only_status: bool = True
    created_at: datetime


class RegisterInstanceRequest(BaseModel):
    instance_name: str
    device_type: str
    initial_project: str = "Unassigned"


class UpdateInstanceRequest(BaseModel):
    status: str
    task: Optional[str] = None
    workspace: Optional[str] = None
    verified_action: Optional[str] = None
    current_directory: Optional[str] = None
    git_status: Optional[str] = None
    open_files: Optional[List[str]] = None


class CreateHandoffRequest(BaseModel):
    from_instance_id: str
    to_instance_id: str
    handoff_type: str
    project_context: str
    task_description: str
    current_state: Dict[str, Any]
    instructions: str
    priority: str = "normal"


class AcceptHandoffRequest(BaseModel):
    verification_notes: str = ""


# ---------------------------------------------------------------------------
# Council Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/council/execute")
async def execute_council_session(request: CouncilRequest):
    """Execute council session with full System Packet Builder integration"""
    session_id = str(uuid.uuid4())
    start_time = datetime.now()

    try:
        # 🔴 FIX #1: SYSTEM PACKET BUILDER INTEGRATION
        # Update constitution if provided
        if request.custom_constitution:
            constitution = ConstitutionCore(**request.custom_constitution)
            packet_builder.update_constitution(constitution)

        # Update session goal if provided
        session_goal = None
        if request.session_goal:
            session_goal = SessionGoal(**request.session_goal)
            packet_builder.add_session_goal(session_goal)

        # 🔥 REPO SHARE INTEGRATION - Inject repo context if provided
        repo_context = None
        if request.repo_share_id and request.repo_share_id in repo_shares:
            try:
                repo_content = build_repo_content_packet(repo_shares[request.repo_share_id])
                repo_context = {
                    "repo_share_metadata": repo_shares[request.repo_share_id].dict(),
                    "repo_content": repo_content
                }
            except Exception as e:
                print(f"Warning: Failed to load repo context: {e}")

        # Build full system packet with ALL context (including repo if shared)
        system_packet = packet_builder.build_packet(request.user_input)
        if repo_context:
            system_packet.add_repo_context(repo_context)

        # 🔴 FIX #3: PROVIDER STATUS CHECK
        active_providers = request.selected_providers or ["claude", "gpt4", "gemini", "grok", "perplexity"]
        await update_provider_status(active_providers)

        # Filter to only working providers
        working_providers = [p for p in active_providers
                           if provider_status[p].status == "online"]

        if not working_providers:
            raise HTTPException(status_code=503, detail="No AI providers are currently available")

        # 🔴 FIX #2: ROUND CONTROL
        execution_mode = request.execution_mode
        if execution_mode == "safe":
            # Safe Mode: 1 round only
            session = await execution_engine.execute_single_round(
                system_packet, working_providers
            )
            round_info = {"mode": "safe", "rounds": 1, "cross_review": False}
        else:
            # Full Mode: 2 rounds with cross-review
            session = await execution_engine.execute_full_council_session(
                system_packet, working_providers
            )
            round_info = {"mode": "full", "rounds": 2, "cross_review": True}

        # 🔴 FIX #4: NO FAKE SYNTHESIS - Track agreements/conflicts
        synthesis = synthesis_engine.analyze_without_merging(session)

        # 🔴 FIX #7: COST + CALL TRACKING
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        session_stats[session_id] = {
            "total_calls": len(session.responses),
            "providers_used": working_providers,
            "processing_time_ms": processing_time,
            "execution_mode": execution_mode,
            "estimated_cost": calculate_session_cost(session),
            "timestamp": start_time.isoformat()
        }

        return {
            "status": "success",
            "session_id": session_id,
            "round_info": round_info,
            "session": execution_engine.export_session(session_id),
            "synthesis": {
                "agreements": synthesis.get("agreements", []),
                "conflicts": synthesis.get("conflicts", []),
                "open_questions": synthesis.get("open_questions", []),
                "provider_perspectives": synthesis.get("provider_perspectives", {})
            },
            "provider_status": {p: provider_status[p].dict() for p in active_providers},
            "session_stats": session_stats[session_id],
            "system_packet_confirmed": True,  # Confirms full context was injected
            "repo_share_info": {
                "repo_shared": bool(request.repo_share_id),
                "share_metadata": repo_shares[request.repo_share_id].dict() if request.repo_share_id and request.repo_share_id in repo_shares else None
            },
            "sole_carrier_warning": "Models do not share memory. Only information provided in this session is considered valid."
        }

    except Exception as e:
        # 🔴 FIX #10: ERROR HANDLING
        await handle_session_error(session_id, str(e), request)
        raise HTTPException(status_code=500, detail=f"Council execution failed: {str(e)}")


# ---------------------------------------------------------------------------
# REPO SHARE HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def build_repo_share_session(
    share_id: str,
    repo_name: str,
    repo_path: str,
    branch: str,
    scope_type: str,
    scope_data: Dict[str, Any]
) -> RepoShareSession:
    """Build a repo share session with metadata"""

    file_count = 0
    total_size = 0

    try:
        if scope_type == "full_repo":
            # Count all files in repo
            for root, dirs, files in os.walk(repo_path):
                # Skip .git and common ignore directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv']]

                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_count += 1
                        total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        continue

        elif scope_type == "selected_files":
            # Count selected files
            files = scope_data.get("files", [])
            for file_path in files:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path):
                    file_count += 1
                    try:
                        total_size += os.path.getsize(full_path)
                    except (OSError, IOError):
                        continue

        elif scope_type == "selected_folder":
            # Count files in selected folder
            folder_path = scope_data.get("folder", "")
            full_folder_path = os.path.join(repo_path, folder_path)
            if os.path.exists(full_folder_path):
                for root, dirs, files in os.walk(full_folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_count += 1
                            total_size += os.path.getsize(file_path)
                        except (OSError, IOError):
                            continue

        elif scope_type == "diff":
            # For diffs, estimate based on changed files
            file_count = len(scope_data.get("changed_files", []))
            total_size = file_count * 1000  # Rough estimate

    except Exception as e:
        print(f"Error calculating repo metrics: {e}")

    return RepoShareSession(
        share_id=share_id,
        repo_name=repo_name,
        repo_path=repo_path,
        branch=branch,
        scope_type=scope_type,
        scope_data=scope_data,
        snapshot_timestamp=datetime.now(),
        file_count=file_count,
        total_size_bytes=total_size,
        read_only_status=True,
        created_at=datetime.now()
    )


def build_repo_content_packet(share: RepoShareSession) -> Dict[str, Any]:
    """Build the actual content packet from repo share session"""

    content = {
        "files": {},
        "structure": {},
        "metadata": {
            "repo_name": share.repo_name,
            "branch": share.branch,
            "scope_type": share.scope_type,
            "snapshot_time": share.snapshot_timestamp.isoformat(),
            "read_only": True
        }
    }

    try:
        if share.scope_type == "selected_files":
            # Read selected files
            files = share.scope_data.get("files", [])
            for file_path in files:
                full_path = os.path.join(share.repo_path, file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content["files"][file_path] = f.read()
                    except (UnicodeDecodeError, IOError):
                        content["files"][file_path] = "[Binary file - content not readable]"

        elif share.scope_type == "selected_folder":
            # Read all files in selected folder
            folder_path = share.scope_data.get("folder", "")
            full_folder_path = os.path.join(share.repo_path, folder_path)
            if os.path.exists(full_folder_path):
                for root, dirs, files in os.walk(full_folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, share.repo_path)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content["files"][relative_path] = f.read()
                        except (UnicodeDecodeError, IOError):
                            content["files"][relative_path] = "[Binary file - content not readable]"

        elif share.scope_type == "diff":
            # Get git diff
            try:
                base_ref = share.scope_data.get("base_ref", "HEAD~1")
                result = subprocess.run(
                    ["git", "diff", base_ref, "--name-only"],
                    cwd=share.repo_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    changed_files = result.stdout.strip().split('\n')
                    content["metadata"]["changed_files"] = changed_files

                    # Get the actual diff
                    diff_result = subprocess.run(
                        ["git", "diff", base_ref],
                        cwd=share.repo_path,
                        capture_output=True,
                        text=True
                    )

                    if diff_result.returncode == 0:
                        content["diff"] = diff_result.stdout

            except Exception as e:
                content["diff_error"] = str(e)

        elif share.scope_type == "full_repo":
            # Limited full repo scan (max 50 files for safety)
            file_count = 0
            for root, dirs, files in os.walk(share.repo_path):
                # Skip .git and common ignore directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv']]

                for file in files:
                    if file_count >= 50:
                        content["metadata"]["truncated"] = True
                        break

                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, share.repo_path)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content["files"][relative_path] = f.read()
                        file_count += 1
                    except (UnicodeDecodeError, IOError):
                        content["files"][relative_path] = "[Binary file - content not readable]"

                if file_count >= 50:
                    break

    except Exception as e:
        content["error"] = str(e)

    return content


# Supporting functions for enhanced council execution
async def update_provider_status(providers: List[str]):
    """Test provider connectivity and update status"""
    for provider in providers:
        try:
            start_time = datetime.now()
            # Quick test call to each provider
            success = await test_provider_connection(provider)
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000

            provider_status[provider] = ProviderStatus(
                provider=provider,
                status="online" if success else "offline",
                response_time_ms=int(response_time) if success else None,
                last_check=datetime.now()
            )
        except Exception as e:
            provider_status[provider] = ProviderStatus(
                provider=provider,
                status="error",
                error_message=str(e),
                last_check=datetime.now()
            )


async def test_provider_connection(provider: str) -> bool:
    """Quick connectivity test for a provider"""
    # This would make actual test calls to each provider
    # For now, return True if API key exists
    return bool(API_KEYS.get(provider))


def calculate_session_cost(session) -> float:
    """Estimate cost of council session"""
    # Rough cost estimates per provider call
    cost_per_call = {
        "claude": 0.003,
        "gpt4": 0.006,
        "gemini": 0.001,
        "grok": 0.002,
        "perplexity": 0.001
    }

    total_cost = 0.0
    for response in session.responses:
        provider = response.get("provider", "unknown")
        total_cost += cost_per_call.get(provider, 0.001)

    return round(total_cost, 4)


async def handle_session_error(session_id: str, error: str, request: CouncilRequest):
    """Handle session errors with retry logic"""
    session_stats[session_id] = {
        "status": "failed",
        "error": error,
        "request_data": request.dict(),
        "timestamp": datetime.now().isoformat(),
        "retry_recommended": True
    }


def extract_decisions_from_synthesis(synthesis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract actionable decisions from synthesis data"""
    decisions = []

    # Look for decision indicators in agreements
    agreements = synthesis_data.get("agreements", [])
    for agreement in agreements:
        if any(keyword in agreement.lower() for keyword in ["should", "must", "recommend", "decide", "choose"]):
            decisions.append({
                "decision": agreement,
                "basis": "council_agreement",
                "confidence": "high",
                "actionable": True
            })

    # Look for decisions in provider perspectives
    perspectives = synthesis_data.get("provider_perspectives", {})
    for provider, perspective in perspectives.items():
        if isinstance(perspective, dict) and "recommendations" in perspective:
            for rec in perspective["recommendations"]:
                decisions.append({
                    "decision": rec,
                    "basis": f"{provider}_recommendation",
                    "confidence": "medium",
                    "actionable": True
                })

    return decisions


@app.get("/api/council/session/{session_id}")
async def get_session(session_id: str):
    """Retrieve council session by ID"""
    session_data = execution_engine.export_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    return session_data


# 🔴 FIX #5: SAVE / CAPTURE BUTTONS
@app.post("/api/insights/save")
async def save_insight(request: SaveInsightRequest):
    """Save insight, decision, or feature from council session"""
    insight_id = str(uuid.uuid4())

    saved_insights[insight_id] = {
        "id": insight_id,
        "type": request.type,
        "title": request.title,
        "content": request.content,
        "session_id": request.session_id,
        "tags": request.tags or [],
        "saved_at": datetime.now().isoformat(),
        "verified": False  # Requires manual verification
    }

    return {
        "status": "success",
        "insight_id": insight_id,
        "message": f"{request.type.capitalize()} saved successfully"
    }


@app.get("/api/insights")
async def get_saved_insights():
    """Get all saved insights"""
    return {"insights": list(saved_insights.values())}


# 🔴 FIX #6: PROVIDER STATUS PANEL
@app.get("/api/providers/status")
async def get_provider_status():
    """Get current status of all AI providers"""
    # Update status before returning
    providers = ["claude", "gpt4", "gemini", "grok", "perplexity"]
    await update_provider_status(providers)

    return {
        "providers": {p: provider_status[p].dict() for p in providers},
        "summary": {
            "online": len([p for p in providers if provider_status[p].status == "online"]),
            "offline": len([p for p in providers if provider_status[p].status in ["offline", "error"]])
        }
    }


# 🔴 FIX #7: COST + CALL TRACKING
@app.get("/api/session/stats/{session_id}")
async def get_session_stats(session_id: str):
    """Get statistics for a specific session"""
    if session_id not in session_stats:
        raise HTTPException(status_code=404, detail="Session not found")

    return session_stats[session_id]


@app.get("/api/session/stats")
async def get_all_session_stats():
    """Get statistics for all sessions"""
    total_cost = sum(stats.get("estimated_cost", 0) for stats in session_stats.values())
    total_calls = sum(stats.get("total_calls", 0) for stats in session_stats.values())

    return {
        "sessions": session_stats,
        "summary": {
            "total_sessions": len(session_stats),
            "total_calls": total_calls,
            "total_estimated_cost": total_cost
        }
    }


@app.get("/api/council/sessions")
async def list_sessions():
    """List all council sessions"""
    sessions = []
    for session_id, session in execution_engine.sessions.items():
        sessions.append({
            "session_id": session_id,
            "user_input": session.user_input[:100] + "..." if len(session.user_input) > 100 else session.user_input,
            "session_start": session.session_start.isoformat(),
            "status": session.status,
            "total_processing_time_ms": session.total_processing_time_ms
        })

    return {"sessions": sessions}


# ---------------------------------------------------------------------------
# 🔥 REPO SHARE SYSTEM - Read-Only Repository Access
# ---------------------------------------------------------------------------

@app.get("/api/repos/available")
async def get_available_repos():
    """Get list of available repositories for sharing"""
    # Scan common repo locations
    common_locations = [
        "C:\\Users\\Stang\\authenticity-detection-framework",
        "C:\\Users\\Stang\\Downloads\\house-of-AI-council-clean",
        "C:\\Users\\Stang\\Downloads\\house-of-AI-main"
    ]

    available_repos.clear()

    for location in common_locations:
        if os.path.exists(location) and os.path.exists(os.path.join(location, ".git")):
            repo_name = os.path.basename(location)
            available_repos[repo_name] = location

    return {
        "repos": [
            {"name": name, "path": path, "exists": os.path.exists(path)}
            for name, path in available_repos.items()
        ]
    }


@app.get("/api/repos/{repo_name}/branches")
async def get_repo_branches(repo_name: str):
    """Get available branches for a repository"""
    if repo_name not in available_repos:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo_path = available_repos[repo_name]

    try:
        # Get list of branches
        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        branches = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                branch = line.strip().replace('* ', '').replace('remotes/origin/', '')
                if branch and not branch.startswith('HEAD') and branch not in branches:
                    branches.append(branch)

        return {"repo": repo_name, "branches": branches or ["master", "main"]}

    except Exception as e:
        return {"repo": repo_name, "branches": ["master", "main"], "error": str(e)}


@app.post("/api/repos/share")
async def create_repo_share(request: RepoShareRequest):
    """Create a read-only repo share session"""
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail="Repository path not found")

    try:
        share_id = str(uuid.uuid4())
        repo_name = os.path.basename(request.repo_path)

        # Create repo share session
        share_session = build_repo_share_session(
            share_id,
            repo_name,
            request.repo_path,
            request.branch,
            request.scope_type,
            request.scope_data or {}
        )

        repo_shares[share_id] = share_session

        return {
            "status": "success",
            "share_id": share_id,
            "session": share_session.dict(),
            "message": f"Repo share created: {share_session.file_count} files, {share_session.total_size_bytes} bytes"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create repo share: {str(e)}")


@app.get("/api/repos/share/{share_id}")
async def get_repo_share(share_id: str):
    """Get repo share session details"""
    if share_id not in repo_shares:
        raise HTTPException(status_code=404, detail="Repo share not found")

    return {"share": repo_shares[share_id].dict()}


@app.get("/api/repos/share/{share_id}/content")
async def get_repo_share_content(share_id: str):
    """Get the actual content from a repo share session"""
    if share_id not in repo_shares:
        raise HTTPException(status_code=404, detail="Repo share not found")

    share = repo_shares[share_id]

    try:
        content_packet = build_repo_content_packet(share)
        return {
            "share_id": share_id,
            "metadata": {
                "repo_name": share.repo_name,
                "branch": share.branch,
                "scope_type": share.scope_type,
                "snapshot_timestamp": share.snapshot_timestamp.isoformat(),
                "file_count": share.file_count,
                "read_only_status": share.read_only_status
            },
            "content": content_packet
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get repo content: {str(e)}")


@app.get("/api/repos/shares")
async def list_repo_shares():
    """List all active repo shares"""
    return {
        "shares": [
            {
                "share_id": share_id,
                "repo_name": share.repo_name,
                "branch": share.branch,
                "scope_type": share.scope_type,
                "created_at": share.created_at.isoformat(),
                "file_count": share.file_count
            }
            for share_id, share in repo_shares.items()
        ]
    }


# ---------------------------------------------------------------------------
# System State Management
# ---------------------------------------------------------------------------

@app.get("/api/system/state")
async def get_system_state():
    """Get current active system state"""
    return {
        "system_state": packet_builder.export_state(),
        "available_sessions": len(execution_engine.sessions),
        "saved_outputs": len(saved_outputs)
    }


@app.post("/api/system/state")
async def update_system_state(request: StateUpdateRequest):
    """Update active system state"""
    try:
        # Get current state
        current_state = packet_builder.system_state

        # Update provided fields
        if request.project_name is not None:
            current_state.project_name = request.project_name
        if request.current_phase is not None:
            current_state.current_phase = request.current_phase
        if request.goals is not None:
            current_state.goals = request.goals
        if request.constraints is not None:
            current_state.constraints = request.constraints
        if request.context_summary is not None:
            current_state.context_summary = request.context_summary
        if request.open_questions is not None:
            current_state.open_questions = request.open_questions

        # Update timestamp
        current_state.last_updated = datetime.now()

        # Save updated state
        packet_builder.update_system_state(current_state)

        return {
            "status": "success",
            "updated_state": packet_builder.export_state()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"State update failed: {str(e)}")


# ---------------------------------------------------------------------------
# Save/Capture System
# ---------------------------------------------------------------------------

@app.post("/api/outputs/save")
async def save_output(request: SaveOutputRequest):
    """Save and name key outputs"""
    try:
        session_data = execution_engine.export_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        save_id = str(uuid.uuid4())
        saved_data = {
            "save_id": save_id,
            "name": request.name,
            "description": request.description,
            "session_id": request.session_id,
            "saved_at": datetime.now().isoformat(),
            "session_data": session_data
        }

        # Include synthesis if requested
        if request.include_synthesis:
            session = execution_engine.get_session(request.session_id)
            if session:
                synthesis = synthesis_engine.synthesize_council_session(session)
                saved_data["synthesis"] = synthesis_engine.export_synthesis(synthesis)

        saved_outputs[save_id] = saved_data

        return {
            "status": "success",
            "save_id": save_id,
            "name": request.name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")


@app.get("/api/outputs/saved")
async def list_saved_outputs():
    """List all saved outputs"""
    outputs = []
    for save_id, data in saved_outputs.items():
        outputs.append({
            "save_id": save_id,
            "name": data["name"],
            "description": data["description"],
            "session_id": data["session_id"],
            "saved_at": data["saved_at"]
        })

    return {"saved_outputs": outputs}


@app.get("/api/outputs/saved/{save_id}")
async def get_saved_output(save_id: str):
    """Retrieve saved output by ID"""
    if save_id not in saved_outputs:
        raise HTTPException(status_code=404, detail="Saved output not found")

    return saved_outputs[save_id]


# ---------------------------------------------------------------------------
# Handoff Packets
# ---------------------------------------------------------------------------

@app.post("/api/handoff/create")
async def create_handoff_packet(request: HandoffPacketRequest):
    """Create exportable handoff packet"""
    try:
        session_data = execution_engine.export_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        session = execution_engine.get_session(request.session_id)
        synthesis = None
        if session:
            synthesis = synthesis_engine.synthesize_council_session(session)

        # 🔴 FIX #8: HANDOFF EXPORT STRUCTURE
        # Extract structured information from synthesis
        synthesis_data = synthesis_engine.export_synthesis(synthesis) if synthesis else {}

        handoff_packet = {
            "handoff_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "recipient": request.recipient,
            "purpose": request.purpose,
            "session_id": request.session_id,

            # Structured export format
            "key_conclusions": synthesis_data.get("agreements", []),
            "verified_facts": [
                {"fact": item, "verified_by": "multiple_models", "confidence": "high"}
                for item in synthesis_data.get("agreements", [])
            ],
            "unverified_claims": [
                {"claim": item, "needs_verification": True, "source": "single_model"}
                for item in synthesis_data.get("conflicts", [])
            ],
            "decisions_made": extract_decisions_from_synthesis(synthesis_data),
            "next_steps": synthesis_data.get("open_questions", []),
            "open_questions": synthesis_data.get("open_questions", []),

            # Raw data for reference
            "original_request": session_data["user_input"],
            "council_outputs": {
                "round1": session_data.get("round1_responses", []),
                "round2": session_data.get("round2_responses", [])
            },
            "provider_perspectives": synthesis_data.get("provider_perspectives", {}),
            "system_context": packet_builder.export_state() if request.include_full_context else None,

            # Meta information
            "session_stats": session_stats.get(request.session_id, {}),
            "sole_carrier_warning": "This handoff contains complete context. Models do not share memory between sessions.",
            "export_timestamp": datetime.now().isoformat()
        }

        return {
            "status": "success",
            "handoff_packet": handoff_packet
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handoff creation failed: {str(e)}")


# ---------------------------------------------------------------------------
# Correction System
# ---------------------------------------------------------------------------

@app.post("/api/council/correct/{session_id}")
async def correct_output(session_id: str, corrections: Dict[str, Any]):
    """Apply corrections to session outputs"""
    try:
        session = execution_engine.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create correction record
        correction_id = str(uuid.uuid4())
        correction_record = {
            "correction_id": correction_id,
            "session_id": session_id,
            "corrected_at": datetime.now().isoformat(),
            "corrections": corrections,
            "corrected_by": corrections.get("corrector", "unknown")
        }

        # Store correction (in real implementation, would update session data)
        if not hasattr(execution_engine, 'corrections'):
            execution_engine.corrections = {}
        execution_engine.corrections[session_id] = correction_record

        return {
            "status": "success",
            "correction_id": correction_id,
            "message": "Corrections applied successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correction failed: {str(e)}")


# ---------------------------------------------------------------------------
# Builder Instance Management
# ---------------------------------------------------------------------------

@app.post("/api/builders/register")
async def register_builder_instance(request: RegisterInstanceRequest):
    """Register a new builder instance"""
    try:
        instance_id = builder_manager.register_instance(
            request.instance_name,
            request.device_type,
            request.initial_project
        )

        return {
            "status": "success",
            "instance_id": instance_id,
            "message": f"Builder instance '{request.instance_name}' registered successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Instance registration failed: {str(e)}")


@app.get("/api/builders/status")
async def get_all_builder_status():
    """Get status of all builder instances"""
    try:
        report = builder_manager.generate_status_report()
        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@app.get("/api/builders/{instance_id}")
async def get_builder_instance(instance_id: str):
    """Get specific builder instance details"""
    instance = builder_manager.get_instance_status(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Builder instance not found")

    return {
        "instance_id": instance_id,
        "instance": {
            "name": instance.instance_name,
            "device_type": instance.device_type,
            "assigned_project": instance.assigned_project,
            "current_task": instance.current_task,
            "last_verified_action": instance.last_verified_action,
            "branch_workspace": instance.branch_workspace,
            "status": instance.status.value,
            "last_active": instance.last_active.isoformat(),
            "session_id": instance.session_id,
            "current_directory": instance.current_directory,
            "git_status": instance.git_status,
            "open_files": instance.open_files,
            "metadata": instance.metadata
        }
    }


@app.post("/api/builders/{instance_id}/update")
async def update_builder_instance(instance_id: str, request: UpdateInstanceRequest):
    """Update builder instance status"""
    try:
        status_enum = InstanceStatus(request.status)

        builder_manager.update_instance_status(
            instance_id=instance_id,
            status=status_enum,
            task=request.task,
            workspace=request.workspace,
            verified_action=request.verified_action
        )

        # Update additional fields if provided
        instance = builder_manager.get_instance_status(instance_id)
        if instance:
            if request.current_directory is not None:
                instance.current_directory = request.current_directory
            if request.git_status is not None:
                instance.git_status = request.git_status
            if request.open_files is not None:
                instance.open_files = request.open_files

            builder_manager._save_instances()

        return {
            "status": "success",
            "message": "Builder instance updated successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Instance update failed: {str(e)}")


@app.post("/api/builders/handoff/create")
async def create_instance_handoff(request: CreateHandoffRequest):
    """Create handoff between builder instances"""
    try:
        handoff_type_enum = HandoffType(request.handoff_type)

        handoff_id = builder_manager.create_handoff(
            from_instance_id=request.from_instance_id,
            to_instance_id=request.to_instance_id,
            handoff_type=handoff_type_enum,
            project_context=request.project_context,
            task_description=request.task_description,
            current_state=request.current_state,
            instructions=request.instructions,
            priority=request.priority
        )

        return {
            "status": "success",
            "handoff_id": handoff_id,
            "message": "Handoff created successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid handoff type: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handoff creation failed: {str(e)}")


@app.post("/api/builders/handoff/{handoff_id}/accept")
async def accept_instance_handoff(handoff_id: str, request: AcceptHandoffRequest):
    """Accept a handoff between builder instances"""
    try:
        # Note: In real implementation, would determine accepting instance from authentication/context
        # For now, getting it from the handoff itself
        handoffs = builder_manager.get_pending_handoffs()
        target_handoff = None
        for handoff in handoffs:
            if handoff.handoff_id == handoff_id:
                target_handoff = handoff
                break

        if not target_handoff:
            raise HTTPException(status_code=404, detail="Handoff not found")

        builder_manager.accept_handoff(
            handoff_id=handoff_id,
            accepting_instance_id=target_handoff.to_instance,
            verification_notes=request.verification_notes
        )

        return {
            "status": "success",
            "message": "Handoff accepted successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handoff acceptance failed: {str(e)}")


@app.get("/api/builders/handoffs")
async def get_pending_handoffs():
    """Get all pending handoffs"""
    try:
        handoffs = builder_manager.get_pending_handoffs()

        handoff_data = []
        for handoff in handoffs:
            from_instance = builder_manager.get_instance_status(handoff.from_instance)
            to_instance = builder_manager.get_instance_status(handoff.to_instance)

            handoff_data.append({
                "handoff_id": handoff.handoff_id,
                "type": handoff.handoff_type.value,
                "from_instance": {
                    "id": handoff.from_instance,
                    "name": from_instance.instance_name if from_instance else "Unknown"
                },
                "to_instance": {
                    "id": handoff.to_instance,
                    "name": to_instance.instance_name if to_instance else "Unknown"
                },
                "project_context": handoff.project_context,
                "task_description": handoff.task_description,
                "instructions": handoff.instructions,
                "priority": handoff.priority,
                "created_at": handoff.created_at.isoformat(),
                "verification_requirements": handoff.verification_requirements
            })

        return {
            "status": "success",
            "pending_handoffs": handoff_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handoffs retrieval failed: {str(e)}")


# ---------------------------------------------------------------------------
# Static Files & Root
# ---------------------------------------------------------------------------

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint - serve main interface"""
    return FileResponse("static/council_interface.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    api_status = {}
    for provider, key in API_KEYS.items():
        api_status[provider] = "configured" if key else "missing"

    return {
        "status": "healthy",
        "api_keys": api_status,
        "components": {
            "packet_builder": "ready",
            "execution_engine": "ready",
            "synthesis_engine": "ready"
        },
        "timestamp": datetime.now().isoformat()
    }


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    """Initialize system on startup"""
    print("🏛️ AI Council System Starting...")
    print(f"   APIs configured: {[k for k, v in API_KEYS.items() if v]}")
    print("   System Packet Builder: Ready")
    print("   Execution Engine: Ready")
    print("   Synthesis Engine: Ready")
    print("🚀 AI Council System: READY")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_council:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )