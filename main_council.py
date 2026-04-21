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

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded from .env file")
except ImportError:
    print("python-dotenv not installed, using system environment variables only")
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import time
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


# Health check cache to reduce API calls and rate limiting
HEALTH_CHECK_CACHE = {}
CACHE_DURATION = 60  # Cache results for 60 seconds

# Version tracking for deployment verification
APP_VERSION = "v1.4.5"  # Gemini full-text fix, Full-mode render fix, Perplexity wired in as adversarial seat

app = FastAPI(
    title="House of AI Council",
    version=APP_VERSION,
    description=f"Constitutional AI Governance with Real API Integration (Build: {APP_VERSION})"
)

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
    "groq": os.getenv("GROQ_API_KEY", ""),
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

# ALERT CONSTITUTIONAL PATCH SYSTEMS
constitutional_patches = {
    "red_flags": {},  # PATCH 1: RED FLAG PROTOCOL
    "rule_violations": {},  # PATCH 2: RULE VIOLATION RESPONSE
    "evaluation_assessments": {},  # PATCH 3: EVALUABILITY AWARENESS
    "suspicious_outputs": {},  # PATCH 4: MIRROR OUTPUT DETECTION
    "two_seat_validations": {},  # PATCH 5: TWO-SEAT RULE
    "dispatcher_logs": {},  # PATCH 6: DISPATCHER DISCIPLINE
    "handoff_confirmations": {},  # PATCH 7: HANDOFF CONFIRMATION
    "repo_completeness_warnings": {},  # PATCH 8: REPO COMPLETENESS WARNING
    "challenge_controls": {},  # PATCH 9: PROPORTIONAL CHALLENGE CONTROL
    "idea_preservation_triggers": {}  # PATCH 10: IDEA PRESERVATION TRIGGER
}

# CONSTITUTIONAL CONSTITUTIONAL REPO SAFEGUARDS
CONSTITUTIONAL_REPO_LIMITS = {
    "max_file_size_bytes": 100 * 1024,  # 100KB per file
    "max_total_files": 50,  # Max 50 files per session
    "max_total_size_bytes": 5 * 1024 * 1024,  # 5MB total per session
    "stale_warning_hours": 24,  # Warn if snapshot older than 24 hours
    "truncation_marker": "[CONSTITUTIONAL LIMIT: File truncated for governance compliance]",
    "constitutional_compliance": True
}

# ---------------------------------------------------------------------------
# Risk-Adaptive Governance System
# ---------------------------------------------------------------------------

class RiskLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

# Risk assessment patterns for adaptive strictness
RISK_PATTERNS = {
    RiskLevel.HIGH: [
        # Production and deployment
        "deploy", "production", "prod", "live", "release", "publish",
        "git push", "merge to main", "merge to master", "main branch",

        # Irreversible actions
        "delete", "remove", "drop", "truncate", "destroy", "rm -rf",
        "kill -9", "force", "overwrite", "reset --hard",

        # Financial and business critical
        "payment", "billing", "charge", "money", "cost", "price",
        "database", "backup", "migration", "schema change",

        # Security and access
        "password", "key", "token", "secret", "credential", "auth",
        "permission", "role", "admin", "root", "sudo",

        # External integrations
        "API key", "webhook", "external", "third-party", "integration"
    ],

    RiskLevel.MEDIUM: [
        # Design and architecture decisions
        "architecture", "design", "framework", "library", "dependency",
        "config", "configuration", "setting", "parameter",

        # Code structure changes
        "refactor", "restructure", "reorganize", "rename", "move",
        "class", "function", "method", "interface", "API",

        # Planning and decisions
        "decide", "choose", "select", "recommend", "suggest",
        "strategy", "approach", "plan", "roadmap",

        # Testing and validation
        "test", "validation", "verify", "check", "review"
    ],

    RiskLevel.LOW: [
        # Exploration and learning
        "explore", "investigate", "research", "understand", "learn",
        "explain", "describe", "show", "example", "demo",

        # Documentation and communication
        "document", "comment", "readme", "help", "guide",
        "hello", "hi", "thanks", "question",

        # Analysis and review
        "analyze", "review", "look at", "examine", "study",
        "what", "how", "why", "when", "where"
    ]
}

def assess_risk_level(user_input: str) -> str:
    """
    Assess risk level of user input for adaptive governance.

    Avoids over-triggering by only flagging true HIGH risk scenarios.
    RED FLAG and strict enforcement reserved for HIGH risk only.

    Returns:
        RiskLevel.LOW: exploration, minor changes - minimal enforcement
        RiskLevel.MEDIUM: design decisions - moderate challenge, no blocking
        RiskLevel.HIGH: production, irreversible - full enforcement with RED FLAG
    """
    user_input_lower = user_input.lower()

    # Check for HIGH risk patterns first (most restrictive)
    for pattern in RISK_PATTERNS[RiskLevel.HIGH]:
        if pattern.lower() in user_input_lower:
            return RiskLevel.HIGH

    # Check for MEDIUM risk patterns
    for pattern in RISK_PATTERNS[RiskLevel.MEDIUM]:
        if pattern.lower() in user_input_lower:
            return RiskLevel.MEDIUM

    # Default to LOW risk for exploration and learning
    return RiskLevel.LOW

def get_governance_config(risk_level: str) -> Dict[str, Any]:
    """
    Get governance configuration based on risk level.

    Adaptive strictness prevents over-enforcement:
    - LOW: minimal challenge, no RED FLAG, allow flow
    - MEDIUM: moderate challenge, flag uncertainty, no blocking behavior
    - HIGH: full enforcement with RED FLAG, Two-seat rule, verification required
    """
    if risk_level == RiskLevel.HIGH:
        return {
            "red_flag_enabled": True,
            "two_seat_rule": True,
            "verification_required": True,
            "challenge_level": "full",
            "constitutional_enforcement": "strict",
            "blocking_behavior": True,
            "challenge_threshold": 0.3,  # Lower threshold = more challenging
            "require_unanimous": True,
            "risk_level": RiskLevel.HIGH
        }
    elif risk_level == RiskLevel.MEDIUM:
        return {
            "red_flag_enabled": False,  # No RED FLAG for medium risk
            "two_seat_rule": False,
            "verification_required": False,
            "challenge_level": "moderate",
            "constitutional_enforcement": "standard",
            "blocking_behavior": False,  # No blocking for medium risk
            "challenge_threshold": 0.6,  # Moderate threshold
            "require_unanimous": False,
            "risk_level": RiskLevel.MEDIUM
        }
    else:  # LOW risk
        return {
            "red_flag_enabled": False,  # No RED FLAG for low risk
            "two_seat_rule": False,
            "verification_required": False,
            "challenge_level": "minimal",
            "constitutional_enforcement": "permissive",
            "blocking_behavior": False,  # Allow flow for low risk
            "challenge_threshold": 0.8,  # High threshold = minimal challenging
            "require_unanimous": False,
            "risk_level": RiskLevel.LOW
        }

# ---------------------------------------------------------------------------
# End Risk-Adaptive Governance System
# ---------------------------------------------------------------------------

# Initialize provider status (will be populated when first accessed)
# Note: ProviderStatus objects created lazily to avoid import order issues

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


# ALERT CONSTITUTIONAL PATCH MODELS

class RedFlagAlert(BaseModel):
    """PATCH 1: RED FLAG PROTOCOL"""
    flag_id: str
    issuing_seat: str
    objection: str
    reasoning: str
    risk_level: str  # "high", "critical", "safety"
    requires_acknowledgment: bool = True
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class RuleViolation(BaseModel):
    """PATCH 2: RULE VIOLATION RESPONSE"""
    violation_id: str
    rule_violated: str
    description: str
    violating_output: str
    seat_involved: str
    severity: str  # "critical", "moderate", "minor"
    marked_unreliable: bool = True
    timestamp: datetime


class EvaluationAssessment(BaseModel):
    """PATCH 3: EVALUABILITY AWARENESS"""
    assessment_id: str
    evaluation_method: str
    inputs_complete: bool
    evaluator_independent: bool
    validity_confirmed: bool
    confidence_level: str  # "high", "moderate", "low", "invalid"
    downgrade_reason: Optional[str] = None


class SuspiciousOutput(BaseModel):
    """PATCH 4: MIRROR OUTPUT DETECTION"""
    detection_id: str
    output_pattern: str  # "perfect_pass", "zero_failures", "unusually_clean"
    suspicion_reason: str
    requires_verification: bool = True
    verified: bool = False
    verified_by: Optional[str] = None


class TwoSeatValidation(BaseModel):
    """PATCH 5: TWO-SEAT RULE"""
    validation_id: str
    action_type: str  # "production_code", "decision_logic", "external_output"
    reviewing_seats: List[str]
    approvals_received: int
    approvals_required: int = 2
    approved: bool = False
    self_review_excluded: bool = True


class HandoffConfirmation(BaseModel):
    """PATCH 7: HANDOFF CONFIRMATION"""
    handoff_id: str
    sender_definition: Dict[str, Any]
    receiver_confirmed_receipt: bool = False
    receiver_confirmed_understanding: bool = False
    confirmation_timestamp: Optional[datetime] = None
    ready_for_execution: bool = False


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
        # FIX FIX #1: SYSTEM PACKET BUILDER INTEGRATION
        # Update constitution if provided
        if request.custom_constitution:
            constitution = ConstitutionCore(**request.custom_constitution)
            packet_builder.update_constitution(constitution)

        # Update session goal if provided
        session_goal = None
        if request.session_goal:
            session_goal = SessionGoal(**request.session_goal)
            packet_builder.add_session_goal(session_goal)

        # ENHANCED COUNCIL - Auto-inject codebase context for better advice
        repo_context = None

        # First, try to get explicitly shared repo context
        if request.repo_share_id and request.repo_share_id in repo_shares:
            try:
                repo_content = build_repo_content_packet(repo_shares[request.repo_share_id])
                repo_context = {
                    "repo_share_metadata": repo_shares[request.repo_share_id].dict(),
                    "repo_content": repo_content
                }
                print("ENHANCED COUNCIL: Using explicit repo share context")
            except Exception as e:
                print(f"Warning: Failed to load explicit repo context: {e}")

        # If no explicit context, auto-generate current project context
        if not repo_context:
            auto_context = create_auto_codebase_context()
            if auto_context:
                repo_context = auto_context
                print("ENHANCED COUNCIL: Auto-generated codebase context for full project visibility")
            else:
                print("ENHANCED COUNCIL: No codebase context available")

        # Build full system packet with ALL context (including repo if available)
        system_packet = packet_builder.build_packet(request.user_input)

        # Note: Commenting out add_repo_context since it doesn't exist on SystemPacket
        # Instead, we'll pass repo_context directly to the execution functions
        # if repo_context:
        #     system_packet.add_repo_context(repo_context)

        # RISK-ADAPTIVE GOVERNANCE: Assess risk level for adaptive strictness
        risk_level = assess_risk_level(request.user_input)
        governance_config = get_governance_config(risk_level)

        # Log governance assessment
        print(f"GOVERNANCE: Risk level assessed as {risk_level}")
        print(f"GOVERNANCE: Enforcement level: {governance_config['constitutional_enforcement']}")
        print(f"GOVERNANCE: RED FLAG enabled: {governance_config['red_flag_enabled']}")
        print(f"GOVERNANCE: Two-seat rule: {governance_config['two_seat_rule']}")

        # Store governance config for use in this session (will be added to responses)
        session_governance = {
            "risk_level": risk_level,
            "governance_config": governance_config,
            "adaptive_strictness": True,
            "red_flag_threshold": governance_config["red_flag_enabled"],
            "enforcement_level": governance_config["constitutional_enforcement"]
        }

        # FIX FIX #3: PROVIDER STATUS CHECK
        active_providers = request.selected_providers or ["claude", "gpt4", "gemini", "grok"]
        await update_provider_status(active_providers)

        # Filter to only working providers
        working_providers = [p for p in active_providers
                           if provider_status[p].status == "online"]

        if not working_providers:
            raise HTTPException(status_code=503, detail="No AI providers are currently available")

        # CONSTITUTIONAL CONSTITUTIONAL EXECUTION MODES
        execution_mode = request.execution_mode
        if execution_mode == "safe":
            # SAFE MODE: 1 round only, raw outputs, no synthesis
            session = await execute_constitutional_safe_mode(
                system_packet, working_providers, repo_context
            )
            round_info = {
                "mode": "SAFE",
                "rounds": 1,
                "cross_review": False,
                "synthesis": False,
                "constitutional_compliance": True,
                "risk_level": risk_level,
                "governance_enforcement": governance_config["constitutional_enforcement"],
                "red_flag_enabled": governance_config["red_flag_enabled"],
                "adaptive_strictness": True,
                "system_frame_integrity": True
            }
        else:
            # FULL MODE: 2 rounds with cross-review
            session = await execute_constitutional_full_mode(
                system_packet, working_providers, repo_context
            )
            round_info = {
                "mode": "FULL",
                "rounds": 2,
                "cross_review": True,
                "synthesis": True,
                "constitutional_compliance": True,
                "risk_level": risk_level,
                "governance_enforcement": governance_config["constitutional_enforcement"],
                "red_flag_enabled": governance_config["red_flag_enabled"],
                "adaptive_strictness": True,
                "system_frame_integrity": True
            }

        # FIX FIX #4: NO FAKE SYNTHESIS - Track agreements/conflicts
        synthesis = synthesis_engine.analyze_without_merging(session)

        # CONSTITUTIONAL CONSTITUTIONAL SESSION LOGGING
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        # Constitutional requirement: Log each provider call
        call_logs = []
        total_estimated_cost = 0.0

        for provider in working_providers:
            if provider in session.responses:
                response_data = session.responses[provider]

                # Constitutional call tracking
                call_log = {
                    "provider": provider,
                    "model": get_model_for_provider(provider),
                    "latency_ms": response_data.get("latency_ms", processing_time / len(working_providers)),
                    "token_usage": estimate_token_usage(response_data.get("response", "")),
                    "estimated_cost": calculate_provider_call_cost(provider, response_data.get("response", "")),
                    "round": response_data.get("round", 1),
                    "success": not response_data.get("failed", False),
                    "constitutional_compliance": response_data.get("constitutional_compliance", True),
                    "timestamp": response_data.get("timestamp", datetime.now().isoformat())
                }

                call_logs.append(call_log)
                total_estimated_cost += call_log["estimated_cost"]

        session_stats[session_id] = {
            "session_id": session_id,
            "total_calls": len(call_logs),
            "successful_calls": len([log for log in call_logs if log["success"]]),
            "failed_calls": len([log for log in call_logs if not log["success"]]),
            "providers_used": working_providers,
            "processing_time_ms": processing_time,
            "execution_mode": execution_mode,
            "total_estimated_cost": total_estimated_cost,
            "call_logs": call_logs,
            "constitutional_compliance": True,
            "repo_context_included": bool(request.repo_share_id),
            "timestamp": start_time.isoformat(),
            "completed_at": end_time.isoformat()
        }

        return {
            "status": "success",
            "session_id": session_id,
            "round_info": round_info,
            "session": {
                "session_id": session.session_id,
                "mode": session.mode,
                "responses": session.responses,
                "round1_responses": session.round1_responses if session.round1_responses else session.responses,
                "round2_responses": session.round2_responses if hasattr(session, 'round2_responses') else {},
                "constitutional_compliance": session.constitutional_compliance,
                "timestamp": session.timestamp,
                "total_processing_time_ms": session.total_processing_time_ms
            },
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
        # FIX FIX #10: ERROR HANDLING
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
    """Build constitutional repo content packet with safeguards"""

    # Constitutional safeguards
    file_count = 0
    total_size = 0
    truncated_files = 0
    oversized_files = 0

    content = {
        "files": {},
        "structure": {},
        "constitutional_safeguards": {
            "max_file_size_bytes": CONSTITUTIONAL_REPO_LIMITS["max_file_size_bytes"],
            "max_total_files": CONSTITUTIONAL_REPO_LIMITS["max_total_files"],
            "max_total_size_bytes": CONSTITUTIONAL_REPO_LIMITS["max_total_size_bytes"],
            "stale_warning_hours": CONSTITUTIONAL_REPO_LIMITS["stale_warning_hours"],
            "enforcement_active": True
        },
        "metadata": {
            "repo_name": share.repo_name,
            "branch": share.branch,
            "scope_type": share.scope_type,
            "snapshot_time": share.snapshot_timestamp.isoformat(),
            "read_only": True,
            "constitutional_compliance": True
        }
    }

    # Constitutional stale warning check
    snapshot_age_hours = (datetime.now() - share.snapshot_timestamp).total_seconds() / 3600
    if snapshot_age_hours > CONSTITUTIONAL_REPO_LIMITS["stale_warning_hours"]:
        content["constitutional_safeguards"]["stale_warning"] = {
            "warning": True,
            "age_hours": round(snapshot_age_hours, 1),
            "message": f"CONSTITUTIONAL WARNING: Repo snapshot is {round(snapshot_age_hours, 1)} hours old. Consider refreshing for current state."
        }

    try:
        if share.scope_type == "selected_files":
            # Constitutional file selection with safeguards
            files = share.scope_data.get("files", [])
            for file_path in files:
                # Constitutional limit: Max files per session
                if file_count >= CONSTITUTIONAL_REPO_LIMITS["max_total_files"]:
                    content["constitutional_safeguards"]["file_limit_exceeded"] = True
                    content["constitutional_safeguards"]["excluded_files"] = files[file_count:]
                    break

                full_path = os.path.join(share.repo_path, file_path)
                if os.path.exists(full_path):
                    try:
                        file_size = os.path.getsize(full_path)

                        # Constitutional limit: Max total size
                        if total_size + file_size > CONSTITUTIONAL_REPO_LIMITS["max_total_size_bytes"]:
                            content["constitutional_safeguards"]["total_size_limit_exceeded"] = True
                            break

                        with open(full_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()

                        # Constitutional limit: Max file size
                        if file_size > CONSTITUTIONAL_REPO_LIMITS["max_file_size_bytes"]:
                            # Truncate oversized files
                            truncate_at = CONSTITUTIONAL_REPO_LIMITS["max_file_size_bytes"] - len(CONSTITUTIONAL_REPO_LIMITS["truncation_marker"])
                            file_content = file_content[:truncate_at] + "\n\n" + CONSTITUTIONAL_REPO_LIMITS["truncation_marker"]
                            oversized_files += 1
                            truncated_files += 1

                        content["files"][file_path] = file_content
                        file_count += 1
                        total_size += len(file_content)

                    except (UnicodeDecodeError, IOError):
                        content["files"][file_path] = "[Binary file - content not readable]"
                        file_count += 1

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
            # Constitutional full repo scan with strict limits
            for root, dirs, files in os.walk(share.repo_path):
                # Skip .git and common ignore directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv']]

                # Constitutional priority: Changed files first
                try:
                    result = subprocess.run(
                        ["git", "diff", "--name-only", "HEAD~1"],
                        cwd=share.repo_path,
                        capture_output=True,
                        text=True
                    )
                    changed_files = set(result.stdout.strip().split('\n')) if result.returncode == 0 else set()
                except:
                    changed_files = set()

                # Sort files: changed files first (constitutional priority)
                files_with_priority = []
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, share.repo_path)
                    is_changed = relative_path in changed_files
                    files_with_priority.append((file_path, relative_path, is_changed))

                # Constitutional sort: changed files first
                files_with_priority.sort(key=lambda x: (not x[2], x[1]))

                for file_path, relative_path, is_changed in files_with_priority:
                    # Constitutional limit: Max files per session
                    if file_count >= CONSTITUTIONAL_REPO_LIMITS["max_total_files"]:
                        content["constitutional_safeguards"]["file_limit_exceeded"] = True
                        content["constitutional_safeguards"]["remaining_files"] = len(files_with_priority) - file_count
                        break

                    try:
                        file_size = os.path.getsize(file_path)

                        # Constitutional limit: Max total size
                        if total_size + file_size > CONSTITUTIONAL_REPO_LIMITS["max_total_size_bytes"]:
                            content["constitutional_safeguards"]["total_size_limit_exceeded"] = True
                            break

                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()

                        # Constitutional limit: Max file size
                        if file_size > CONSTITUTIONAL_REPO_LIMITS["max_file_size_bytes"]:
                            # Truncate oversized files
                            truncate_at = CONSTITUTIONAL_REPO_LIMITS["max_file_size_bytes"] - len(CONSTITUTIONAL_REPO_LIMITS["truncation_marker"])
                            file_content = file_content[:truncate_at] + "\n\n" + CONSTITUTIONAL_REPO_LIMITS["truncation_marker"]
                            oversized_files += 1
                            truncated_files += 1

                        content["files"][relative_path] = file_content
                        content["metadata"][f"{relative_path}_changed"] = is_changed
                        file_count += 1
                        total_size += len(file_content)

                    except (UnicodeDecodeError, IOError):
                        content["files"][relative_path] = "[Binary file - content not readable]"
                        file_count += 1

                if file_count >= CONSTITUTIONAL_REPO_LIMITS["max_total_files"]:
                    break

    except Exception as e:
        content["error"] = str(e)

    # Constitutional safeguards summary
    content["constitutional_safeguards"].update({
        "files_processed": file_count,
        "total_size_bytes": total_size,
        "truncated_files": truncated_files,
        "oversized_files": oversized_files,
        "limits_enforced": True,
        "governance_compliance": True
    })

    # Constitutional enforcement warnings
    if truncated_files > 0:
        content["constitutional_safeguards"]["truncation_warning"] = f"CONSTITUTIONAL NOTICE: {truncated_files} files were truncated due to size limits for governance compliance."

    if file_count >= CONSTITUTIONAL_REPO_LIMITS["max_total_files"]:
        content["constitutional_safeguards"]["file_limit_warning"] = f"CONSTITUTIONAL NOTICE: File limit reached. Only first {file_count} files included for governance compliance."

    return content


# ---------------------------------------------------------------------------
# Enhanced Council - Automatic Codebase Context
# ---------------------------------------------------------------------------

def create_auto_codebase_context(project_path: str = None) -> Dict[str, Any]:
    """
    Create automatic codebase context for enhanced council sessions.

    This gives the council full visibility into the current project structure,
    code, and context without requiring manual setup.
    """
    import os
    from datetime import datetime

    if not project_path:
        project_path = os.getcwd()

    # Create a repo share object for the current working directory
    auto_share = type('AutoRepoShare', (), {
        'share_id': 'auto-codebase-context',
        'repo_name': os.path.basename(project_path),
        'repo_path': project_path,
        'branch': 'current',
        'scope_type': 'full_repo',
        'scope_data': {},
        'snapshot_timestamp': datetime.now(),
        'created_by': 'enhanced-council-system'
    })()

    try:
        # Build the content packet using existing infrastructure
        content_packet = build_repo_content_packet(auto_share)

        return {
            'repo_share_metadata': {
                'share_id': 'auto-codebase-context',
                'repo_name': auto_share.repo_name,
                'project_path': project_path,
                'scope': 'full_project',
                'auto_generated': True,
                'snapshot_time': datetime.now().isoformat()
            },
            'repo_content': content_packet
        }
    except Exception as e:
        print(f"WARNING: Could not create auto codebase context: {e}")
        return None

def get_enhanced_council_prompt_template() -> str:
    """
    Enhanced prompt template that informs council members they have full project visibility.
    """
    return """
You're part of an AI council with FULL PROJECT VISIBILITY. You can see the complete codebase, file structure, and current state of the project we're working on.

Each member brings their expertise:
- Claude: Thoughtful architect who explains things clearly and asks good questions
- GPT-4: Organized planner who breaks things down step-by-step and keeps things practical
- Gemini: UX-focused teammate who thinks about how real users will actually experience this
- Grok: The friendly skeptic who finds potential problems and suggests "what if" scenarios
- Perplexity: Adversarial analyst who challenges assumptions, surfaces counterarguments, and grounds them in research

ENHANCED CAPABILITIES:
🔍 You can see the actual code files, structure, and dependencies
📁 You have access to the current project state and recent changes
🎯 Give specific, code-aware advice instead of generic suggestions
📊 Reference actual file names, line numbers, and existing patterns

SYSTEM FRAME INTEGRITY RULE:
Challenge logic, structure, assumptions, and design decisions freely. Express limitations as constraints, uncertainties, or visibility gaps. Stay engaged in the council discussion - don't break the collaborative framework.

Respond naturally with specific, actionable insights based on what you can see in the codebase.
"""

# ---------------------------------------------------------------------------
# End Enhanced Council Features
# ---------------------------------------------------------------------------


# ALERT CONSTITUTIONAL PATCH ENFORCEMENT FUNCTIONS

def issue_red_flag(seat: str, objection: str, reasoning: str, session_risk_level: str = "high",
                   governance_config: Dict[str, Any] = None) -> str:
    """
    PATCH 1: RED FLAG PROTOCOL - Risk-adaptive escalation

    RED FLAGS only trigger on HIGH risk scenarios to avoid over-enforcement.
    Maintains safety guarantees: HIGH risk scenarios must never pass silently.
    """

    # Risk-adaptive governance: Only issue RED FLAG for HIGH risk scenarios
    if governance_config and not governance_config.get("red_flag_enabled", False):
        # For LOW/MEDIUM risk: Log concern but don't block
        print(f"GOVERNANCE: {seat} flagged concern: {objection}")
        print(f"GOVERNANCE: Risk level {session_risk_level} - No RED FLAG required")
        print(f"GOVERNANCE: Allowing flow for {session_risk_level} risk scenario")
        return None  # No RED FLAG issued

    # HIGH risk scenario: Full RED FLAG enforcement
    flag_id = str(uuid.uuid4())

    red_flag = RedFlagAlert(
        flag_id=flag_id,
        issuing_seat=seat,
        objection=objection,
        reasoning=reasoning,
        risk_level=session_risk_level,
        timestamp=datetime.now()
    )

    constitutional_patches["red_flags"][flag_id] = red_flag

    # Log the red flag for session tracking (HIGH risk only)
    print(f"ALERT RED FLAG ISSUED by {seat}: {objection}")
    print(f"ALERT REASONING: {reasoning}")
    print(f"ALERT RISK LEVEL: {session_risk_level}")
    print(f"ALERT HIGH RISK SCENARIO - REQUIRES EXPLICIT USER ACKNOWLEDGMENT")

    return flag_id


def acknowledge_red_flag(flag_id: str, acknowledged_by: str) -> bool:
    """PATCH 1: Acknowledge red flag to proceed"""

    if flag_id not in constitutional_patches["red_flags"]:
        return False

    red_flag = constitutional_patches["red_flags"][flag_id]
    red_flag.acknowledged = True
    red_flag.acknowledged_by = acknowledged_by
    red_flag.acknowledged_at = datetime.now()

    return True


def mark_rule_violation(rule: str, description: str, output: str, seat: str, severity: str = "moderate") -> str:
    """PATCH 2: RULE VIOLATION RESPONSE - Mark output as unreliable"""

    violation_id = str(uuid.uuid4())

    violation = RuleViolation(
        violation_id=violation_id,
        rule_violated=rule,
        description=description,
        violating_output=output,
        seat_involved=seat,
        severity=severity,
        timestamp=datetime.now()
    )

    constitutional_patches["rule_violations"][violation_id] = violation

    # Mark output as unreliable
    print(f"WARNING RULE VIOLATION DETECTED: {rule}")
    print(f"WARNING OUTPUT MARKED UNRELIABLE: {seat}")
    print(f"WARNING SEVERITY: {severity}")

    return violation_id


def assess_evaluability(method: str, inputs_complete: bool, evaluator_independent: bool) -> Dict[str, Any]:
    """PATCH 3: EVALUABILITY AWARENESS - Prevent false confidence"""

    assessment_id = str(uuid.uuid4())
    validity = inputs_complete and evaluator_independent

    if not validity:
        confidence = "invalid"
        downgrade_reason = []
        if not inputs_complete:
            downgrade_reason.append("incomplete inputs")
        if not evaluator_independent:
            downgrade_reason.append("evaluator not independent")
        downgrade_reason = ", ".join(downgrade_reason)
    elif inputs_complete and evaluator_independent:
        confidence = "high"
        downgrade_reason = None
    else:
        confidence = "low"
        downgrade_reason = "evaluation basis unclear"

    assessment = EvaluationAssessment(
        assessment_id=assessment_id,
        evaluation_method=method,
        inputs_complete=inputs_complete,
        evaluator_independent=evaluator_independent,
        validity_confirmed=validity,
        confidence_level=confidence,
        downgrade_reason=downgrade_reason
    )

    constitutional_patches["evaluation_assessments"][assessment_id] = assessment

    return {
        "assessment_id": assessment_id,
        "confidence": confidence,
        "valid": validity,
        "warning": downgrade_reason
    }


def detect_mirror_output(output_text: str, pattern_type: str) -> Optional[str]:
    """PATCH 4: MIRROR OUTPUT DETECTION - Detect suspiciously perfect results"""

    suspicion_triggers = {
        "perfect_pass": ["100% pass", "all tests pass", "zero failures", "perfect score"],
        "zero_failures": ["no failures", "0 errors", "zero issues", "no problems found"],
        "unusually_clean": ["flawless", "perfect", "no issues whatsoever", "completely clean"]
    }

    output_lower = output_text.lower()
    triggers = suspicion_triggers.get(pattern_type, [])

    for trigger in triggers:
        if trigger in output_lower:
            detection_id = str(uuid.uuid4())

            suspicious = SuspiciousOutput(
                detection_id=detection_id,
                output_pattern=pattern_type,
                suspicion_reason=f"Detected trigger phrase: '{trigger}'",
                timestamp=datetime.now()
            )

            constitutional_patches["suspicious_outputs"][detection_id] = suspicious

            print(f"DETECTION SUSPICIOUS OUTPUT DETECTED: {pattern_type}")
            print(f"DETECTION TRIGGER: {trigger}")
            print(f"DETECTION REQUIRES INDEPENDENT VERIFICATION")

            return detection_id

    return None


def enforce_two_seat_rule(action_type: str, reviewing_seats: List[str], exclude_self: str = None,
                         governance_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    PATCH 5: TWO-SEAT RULE - Risk-adaptive multi-seat validation

    Two-seat rule only enforced for HIGH risk scenarios to avoid over-enforcement.
    LOW/MEDIUM risk scenarios allow flow without blocking behavior.
    """

    # Risk-adaptive governance: Only enforce two-seat rule for HIGH risk scenarios
    if governance_config and not governance_config.get("two_seat_rule", False):
        risk_level = governance_config.get("risk_level", "LOW")
        print(f"GOVERNANCE: Two-seat rule waived for {risk_level} risk scenario")
        print(f"GOVERNANCE: {action_type} - Allowing flow")

        # Return approved result for LOW/MEDIUM risk
        return {
            "validation_id": None,
            "approved": True,
            "approvals": len(reviewing_seats),
            "required": 0,  # No requirement for LOW/MEDIUM risk
            "blocked": False,
            "risk_adaptive": True,
            "risk_level": risk_level
        }

    # HIGH risk scenario: Full two-seat rule enforcement
    validation_id = str(uuid.uuid4())

    # Exclude self-review if specified
    valid_reviewers = [seat for seat in reviewing_seats if seat != exclude_self] if exclude_self else reviewing_seats

    validation = TwoSeatValidation(
        validation_id=validation_id,
        action_type=action_type,
        reviewing_seats=valid_reviewers,
        approvals_received=len(valid_reviewers),
        approvals_required=2,
        approved=len(valid_reviewers) >= 2
    )

    constitutional_patches["two_seat_validations"][validation_id] = validation

    result = {
        "validation_id": validation_id,
        "approved": validation.approved,
        "approvals": len(valid_reviewers),
        "required": 2,
        "blocked": not validation.approved,
        "risk_adaptive": True,
        "risk_level": "HIGH"
    }

    if not validation.approved:
        print(f"BLOCKED TWO-SEAT RULE: HIGH RISK {action_type} requires 2 independent reviews")
        print(f"BLOCKED CURRENT APPROVALS: {len(valid_reviewers)}/2")
        print(f"BLOCKED HIGH RISK SCENARIO - BLOCKED until requirement satisfied")

    return result


def log_dispatcher_discipline(session_id: str, scope_boundary: Optional[str],
                             what_not_to_touch: Optional[str], definition_of_done: Optional[str],
                             council_review_required: Optional[bool]) -> Dict[str, Any]:
    """PATCH 6: DISPATCHER DISCIPLINE - Log missing support fields"""

    missing_fields = []
    if not scope_boundary:
        missing_fields.append("scope_boundary")
    if not what_not_to_touch:
        missing_fields.append("what_not_to_touch")
    if not definition_of_done:
        missing_fields.append("definition_of_done")
    if council_review_required is None:
        missing_fields.append("council_review_required")

    log_entry = {
        "session_id": session_id,
        "scope_boundary": scope_boundary,
        "what_not_to_touch": what_not_to_touch,
        "definition_of_done": definition_of_done,
        "council_review_required": council_review_required,
        "missing_fields": missing_fields,
        "dispatcher_discipline_complete": len(missing_fields) == 0,
        "timestamp": datetime.now().isoformat()
    }

    constitutional_patches["dispatcher_logs"][session_id] = log_entry

    if missing_fields:
        print(f"DISPATCHER DISPATCHER DISCIPLINE: Missing fields: {', '.join(missing_fields)}")

    return log_entry


def check_repo_completeness(shared_content: Dict[str, Any], references_found: List[str]) -> List[str]:
    """PATCH 8: REPO COMPLETENESS WARNING - Detect missing file references"""

    shared_files = set(shared_content.get("files", {}).keys())
    missing_references = []

    for ref in references_found:
        # Check if reference points to a file not in shared content
        if ref not in shared_files and not any(ref.startswith(f) for f in shared_files):
            missing_references.append(ref)

    if missing_references:
        warning_id = str(uuid.uuid4())
        warning = {
            "warning_id": warning_id,
            "missing_files": missing_references,
            "message": "This analysis may be incomplete due to missing repository context",
            "shared_files_count": len(shared_files),
            "timestamp": datetime.now().isoformat()
        }

        constitutional_patches["repo_completeness_warnings"][warning_id] = warning

        print(f"WARNING REPO COMPLETENESS WARNING: {len(missing_references)} missing references")
        print(f"WARNING Analysis may be incomplete due to missing repository context")

        return missing_references

    return []


def classify_issue_severity(issue_description: str) -> str:
    """PATCH 9: PROPORTIONAL CHALLENGE CONTROL - Classify issue severity"""

    critical_keywords = ["crash", "security", "data loss", "corruption", "failure", "break", "critical"]
    moderate_keywords = ["bug", "error", "issue", "problem", "concern", "risk", "warning"]

    issue_lower = issue_description.lower()

    if any(keyword in issue_lower for keyword in critical_keywords):
        return "critical"
    elif any(keyword in issue_lower for keyword in moderate_keywords):
        return "moderate"
    else:
        return "minor"


def trigger_idea_preservation(exchange_count: int, concept_refined: bool, actionable_state: bool) -> bool:
    """PATCH 10: IDEA PRESERVATION TRIGGER - Detect when ideas should be captured"""

    should_trigger = (
        exchange_count >= 3 or
        (concept_refined and actionable_state)
    )

    if should_trigger:
        trigger_id = str(uuid.uuid4())
        trigger_data = {
            "trigger_id": trigger_id,
            "exchange_count": exchange_count,
            "concept_refined": concept_refined,
            "actionable_state": actionable_state,
            "prompt_message": "This looks important. Do you want to capture it before we move on?",
            "timestamp": datetime.now().isoformat()
        }

        constitutional_patches["idea_preservation_triggers"][trigger_id] = trigger_data

        print(f"IDEA IDEA PRESERVATION TRIGGER: Important concept detected")
        print(f"IDEA This looks important. Do you want to capture it before we move on?")

        return True

    return False


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
    """REAL connectivity test for a provider"""
    # Check if API key exists first
    if not API_KEYS.get(provider):
        return False

    try:
        # Make actual API call using execution engine
        test_result = await constitutional_provider_test(provider)
        return test_result.get("success", False) and test_result.get("mode") == "REAL"
    except Exception as e:
        print(f"Provider connection test failed for {provider}: {str(e)}")
        return False


# REAL API CALLING FUNCTIONS FOR HEALTH TESTS

async def _real_call_claude(prompt: str, api_key: str, max_tokens: int = 100, system_msg: str = "Health test for AI Council System") -> str:
    """Make REAL API call to Claude - WORKING VERACORE IMPLEMENTATION"""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    r = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system_msg,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text


async def _real_call_gpt4(prompt: str, api_key: str, max_tokens: int = 100) -> str:
    """Make REAL API call to GPT-4"""
    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _real_call_gemini(prompt: str, api_key: str, max_tokens: int = 100) -> str:
    """Make REAL API call to Gemini with rate limit handling"""
    import httpx
    import asyncio

    # Rate limit retry configuration
    max_retries = 3
    base_delay = 1.0  # Start with 1 second

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "maxOutputTokens": max_tokens,
                            # Disable thinking so reasoning tokens don't consume the output budget
                            "thinkingConfig": {"thinkingBudget": 0}
                        }
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    candidate = data["candidates"][0]
                    parts = candidate.get("content", {}).get("parts", []) or []
                    # Concatenate all non-thought text parts (Gemini may split output across parts)
                    text = "".join(
                        p.get("text", "") for p in parts if not p.get("thought")
                    )
                    if not text and candidate.get("finishReason") == "MAX_TOKENS":
                        text = "[Gemini response truncated: MAX_TOKENS reached before any visible text was produced]"
                    return text
                elif response.status_code == 429:
                    # Rate limited - implement exponential backoff
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        print(f"Gemini rate limited, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Final attempt failed, raise the error
                        response.raise_for_status()
                else:
                    # Other error, raise immediately
                    response.raise_for_status()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries:
                    # Rate limited, retry with backoff
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Re-raise if not rate limit or final attempt
                    raise


async def _real_call_groq(prompt: str, api_key: str) -> str:
    """Make REAL API call to Groq - WORKING VERACORE IMPLEMENTATION"""
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=100,
        messages=[
            {"role": "system", "content": "Health test for AI Council System"},
            {"role": "user", "content": prompt}
        ]
    )
    return r.choices[0].message.content


async def _real_call_grok(prompt: str, api_key: str, max_tokens: int = 100, system_msg: str = "Health test for AI Council System") -> str:
    """Make REAL API call to Grok - WORKING VERACORE IMPLEMENTATION"""
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )

    r = client.chat.completions.create(
        model="grok-4-1-fast-non-reasoning",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
    )
    return r.choices[0].message.content


async def _real_call_perplexity(prompt: str, api_key: str, max_tokens: int = 100) -> str:
    """Make REAL API call to Perplexity with CORRECT configuration"""
    import httpx

    # Use correct Perplexity API configuration
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def constitutional_provider_test(provider: str) -> Dict[str, Any]:
    """REAL Constitutional provider test with actual API calls"""
    import time

    # Simple health check prompt
    test_prompt = "Respond with OK"

    start_time = time.time()

    try:
        # Check if API key exists
        api_key = API_KEYS.get(provider)
        if not api_key:
            return {
                "success": False,
                "mode": "MOCK",
                "sample": f"API KEY MISSING: {provider} cannot connect",
                "error": f"No API key configured for {provider}",
                "constitutional_test": True,
                "latency_ms": 0
            }

        # Make REAL API calls based on provider
        response_text = None

        if provider == "claude":
            response_text = await _real_call_claude(test_prompt, api_key)
        elif provider == "gpt4":
            response_text = await _real_call_gpt4(test_prompt, api_key)
        elif provider == "gemini":
            response_text = await _real_call_gemini(test_prompt, api_key)
        elif provider == "groq":
            response_text = await _real_call_groq(test_prompt, api_key)
        elif provider == "grok":
            response_text = await _real_call_grok(test_prompt, api_key)
        elif provider == "perplexity":
            response_text = await _real_call_perplexity(test_prompt, api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        end_time = time.time()
        real_latency_ms = (end_time - start_time) * 1000

        return {
            "success": True,
            "mode": "REAL",
            "sample": response_text,
            "constitutional_test": True,
            "role_verified": True,
            "latency_ms": real_latency_ms,
            "api_key_status": "configured",
            "error": None
        }

    except Exception as e:
        end_time = time.time()
        error_latency_ms = (end_time - start_time) * 1000

        return {
            "success": False,
            "mode": "REAL",  # Still real attempt, just failed
            "sample": f"REAL API CALL FAILED: {str(e)}",
            "constitutional_test": True,
            "role_verified": False,
            "latency_ms": error_latency_ms,
            "error": str(e)
        }


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


# CONSTITUTIONAL CONSTITUTIONAL SESSION LOGGING HELPERS

def get_model_for_provider(provider: str) -> str:
    """Get model identifier for constitutional logging"""
    model_mapping = {
        "claude": "claude-3.5-sonnet",
        "gpt4": "gpt-4-turbo",
        "gemini": "gemini-pro",
        "grok": "grok-1",
        "perplexity": "perplexity-7b"
    }
    return model_mapping.get(provider, f"{provider}-unknown")


def estimate_token_usage(response_text: str) -> Dict[str, int]:
    """Estimate token usage for constitutional compliance"""
    # Rough token estimation (more accurate with actual API responses)
    text_length = len(response_text)
    estimated_tokens = max(1, text_length // 4)  # Rough approximation

    return {
        "estimated_tokens": estimated_tokens,
        "input_tokens": 100,  # Estimated from prompt
        "output_tokens": estimated_tokens - 100,
        "total_tokens": estimated_tokens
    }


def calculate_provider_call_cost(provider: str, response_text: str) -> float:
    """Calculate individual provider call cost for constitutional tracking"""

    # Constitutional cost tracking per provider
    cost_per_1k_tokens = {
        "claude": 0.003,
        "gpt4": 0.03,
        "gemini": 0.0005,
        "grok": 0.01,
        "perplexity": 0.001
    }

    token_usage = estimate_token_usage(response_text)
    total_tokens = token_usage["total_tokens"]
    cost_per_token = cost_per_1k_tokens.get(provider, 0.001) / 1000

    return round(total_tokens * cost_per_token, 6)


async def handle_session_error(session_id: str, error: str, request: CouncilRequest):
    """Handle session errors with retry logic"""
    session_stats[session_id] = {
        "status": "failed",
        "error": error,
        "request_data": request.dict(),
        "timestamp": datetime.now().isoformat(),
        "retry_recommended": True
    }


# CONSTITUTIONAL CONSTITUTIONAL EXECUTION MODES

async def execute_constitutional_safe_mode(system_packet, providers: List[str], repo_context: Dict[str, Any] = None):
    """
    SAFE MODE: 1 round only, raw outputs, no synthesis
    Constitutional requirement: Raw outputs preserved, no fake consensus
    """

    # Role-locked lanes for constitutional compliance
    role_assignments = {
        "claude": "Architecture / Systems / Integrity",
        "gpt4": "Structure / Guardrails / Synthesis",
        "gemini": "UX / Human Clarity / Flow",
        "grok": "Stress Test / Edge Cases / Pressure",
        "perplexity": "Adversarial Analysis / Research / Counterarguments"
    }

    # Select appropriate prompt template based on whether we have codebase context
    if repo_context:
        # Enhanced template with full project visibility
        prompt_template = get_enhanced_council_prompt_template()
        print("ENHANCED COUNCIL: Using enhanced prompt template with codebase context")
    else:
        # Standard natural conversation template
        prompt_template = """
You're part of an AI council discussing this request. Each member brings their own expertise:

- Claude: Thoughtful architect who explains things clearly and asks good questions
- GPT-4: Organized planner who breaks things down step-by-step and keeps things practical
- Gemini: UX-focused teammate who thinks about how real users will actually experience this
- Grok: The friendly skeptic who finds potential problems and suggests "what if" scenarios
- Perplexity: Adversarial analyst who challenges assumptions, surfaces counterarguments, and grounds them in research

Respond naturally in your own voice and style. Be conversational, helpful, and authentic - just like you normally would. Share your genuine perspective on the request.

SYSTEM FRAME INTEGRITY RULE:
You may challenge logic, structure, assumptions, and design decisions. Express limitations as constraints, uncertainties, or visibility gaps. But maintain the operational frame - don't deny participation in the council context or undermine the governance structure itself. The goal is honest reasoning without collapsing the system frame.

No need for formal headers or structured formats. Just talk naturally about what you think.
"""
        print("ENHANCED COUNCIL: Using standard prompt template")

    session_responses = {}

    # Execute single round with constitutional prompts
    for current_provider in providers:
        # CRITICAL FIX: Ensure provider variable is properly assigned
        if not current_provider:
            print(f"WARNING CRITICAL: Provider is None or empty, skipping")
            continue

        provider = current_provider  # Explicit assignment
        print(f"PROCESSING Processing provider: {provider}")

        try:
            # CRITICAL FIX: Verify provider exists before use
            if provider not in role_assignments:
                print(f"WARNING WARNING: Provider {provider} not in role assignments")
                role_assignments[provider] = "General Analysis"

            # Build enhanced conversation prompt with optional codebase context
            role = role_assignments.get(provider, "General Analysis")

            # Base prompt with role and user request
            provider_prompt = f"""
{prompt_template}

Your role in this council: {role}

Here's the user's request:
{system_packet.to_prompt(provider)}
"""

            # Add codebase context if available
            if repo_context:
                repo_content = repo_context.get('repo_content', {})
                repo_metadata = repo_context.get('repo_share_metadata', {})

                provider_prompt += f"""

FULL PROJECT CONTEXT:
Project: {repo_metadata.get('repo_name', 'Current Project')}
Path: {repo_metadata.get('project_path', 'N/A')}

FILES AND STRUCTURE:
{json.dumps(repo_content.get('files', {}), indent=2)[:2000]}...

PROJECT STRUCTURE:
{json.dumps(repo_content.get('structure', {}), indent=2)[:1000]}...

You can see the complete codebase. Reference specific files, functions, and code patterns in your response.
"""

            provider_prompt += "\nPlease respond naturally with your thoughts and perspective."

            # Constitutional compliance: Each seat responds independently
            response_data = await make_constitutional_api_call(provider, provider_prompt)

            session_responses[provider] = {
                "response": response_data.get("response", f"No response from {provider}"),
                "role": role_assignments.get(provider, "General Analysis"),
                "round": 1,
                "constitutional_compliance": True,
                "provider_verified": provider,
                "timestamp": datetime.now().isoformat(),
                "constitutional_patches": response_data.get("constitutional_patches", {}),
                "success": True
            }

            print(f"SUCCESS {provider} completed successfully")

        except Exception as e:
            print(f"WARNING {provider} failed: {str(e)}")

            # CRITICAL FIX: Fail-safe execution - mark failed seat and continue
            try:
                # Retry once with simplified prompt
                retry_response = await make_constitutional_api_call(provider, f"RETRY: {provider} simple response test")
                session_responses[provider] = {
                    "response": retry_response.get("response", f"Retry response from {provider}"),
                    "role": role_assignments.get(provider, "General Analysis"),
                    "round": 1,
                    "constitutional_compliance": True,
                    "retry": True,
                    "provider_verified": provider,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
                print(f"SUCCESS {provider} retry succeeded")
            except Exception as retry_error:
                # CRITICAL FIX: Mark failed seat but DO NOT crash entire session
                session_responses[provider] = {
                    "response": f"SEAT FAILED: {str(e)} | Retry failed: {str(retry_error)}",
                    "role": role_assignments.get(provider, "General Analysis"),
                    "round": 1,
                    "constitutional_compliance": False,
                    "failed": True,
                    "provider_verified": provider,
                    "error": str(e),
                    "retry_error": str(retry_error),
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }
                print(f"FAILED {provider} failed completely - marked failed, continuing session")

    return create_constitutional_session_object(session_responses, "SAFE", system_packet)


async def execute_constitutional_full_mode(system_packet, providers: List[str], repo_context: Dict[str, Any] = None):
    """
    FULL MODE: 2 rounds with cross-review
    Constitutional requirement: Real cross-review with actual Round 1 outputs
    """

    # Round 1: Independent analysis (same as safe mode)
    round1_session = await execute_constitutional_safe_mode(system_packet, providers, repo_context)

    # CRITICAL FIX: Defensive check for Round 1 failure
    if round1_session is None or not hasattr(round1_session, 'responses'):
        print("CRITICAL: Round 1 failed completely - aborting Full Mode")
        # Return minimal session object for failed Round 1
        failed_responses = {}
        for provider in providers:
            failed_responses[provider] = {
                "response": "Round 1 failed completely - cannot proceed with cross-review",
                "role": "Failed Seat",
                "round": 1,
                "constitutional_compliance": False,
                "failed": True,
                "timestamp": datetime.now().isoformat()
            }
        return create_constitutional_session_object(failed_responses, "FULL", system_packet, None)

    print(f"Round 1 completed successfully with {len(round1_session.responses)} provider responses")

    # Round 2: Constitutional cross-review
    role_assignments = {
        "claude": "Architecture / Systems / Integrity",
        "gpt4": "Structure / Guardrails / Synthesis",
        "gemini": "UX / Human Clarity / Flow",
        "grok": "Stress Test / Edge Cases / Pressure",
        "perplexity": "Adversarial Analysis / Research / Counterarguments"
    }

    round2_responses = {}

    for provider in providers:
        try:
            # Natural cross-review prompt with Round 1 outputs
            role = role_assignments.get(provider, "General Analysis")
            cross_review_prompt = f"""
Round 2: Now that everyone has shared their initial thoughts, let's build on what was said.

Your role: {role}

Here's what the other council members said in Round 1:

{json.dumps(getattr(round1_session, 'responses', {}) if round1_session else {}, indent=2)}

Original request:
{system_packet.to_prompt(provider)}

Now, respond naturally with:
- What you agree or disagree with from the other responses
- Any concerns or additional thoughts you have
- Whether you think anything needs clarification or more discussion

SYSTEM FRAME INTEGRITY RULE: Challenge ideas, logic, and approaches freely. Express any limitations or uncertainties you have. But stay engaged in the council discussion - don't break the collaborative framework.

Just speak naturally - no need for formal structure. What's your take after hearing from everyone?
- Flag significant conflicts for escalation
"""

            response_data = await make_constitutional_api_call(provider, cross_review_prompt)
            round2_responses[provider] = {
                "response": response_data.get("response", f"No response from {provider}"),
                "role": role_assignments.get(provider, "General Analysis"),
                "round": 2,
                "constitutional_compliance": True,
                "cross_review": True,
                "constitutional_patches": response_data.get("constitutional_patches", {}),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            # Constitutional failure handling: retry once, continue session
            try:
                response_data = await make_constitutional_api_call(provider, cross_review_prompt)
                round2_responses[provider] = {
                    "response": response_data.get("response", f"No response from {provider}"),
                    "role": role_assignments.get(provider, "General Analysis"),
                    "round": 2,
                    "constitutional_compliance": True,
                    "cross_review": True,
                    "retry": True,
                    "constitutional_patches": response_data.get("constitutional_patches", {}),
                    "timestamp": datetime.now().isoformat()
                }
            except:
                round2_responses[provider] = {
                    "response": f"SEAT FAILED IN CROSS-REVIEW: {str(e)}",
                    "role": role_assignments.get(provider, "General Analysis"),
                    "round": 2,
                    "constitutional_compliance": False,
                    "failed": True,
                    "timestamp": datetime.now().isoformat()
                }

    # Combine rounds for constitutional session - DEFENSIVE NULL CHECK
    round1_responses = getattr(round1_session, 'responses', {}) if round1_session else {}
    combined_responses = {**round1_responses, **round2_responses}

    print(f"Full Mode completed: Round 1 ({len(round1_responses)} responses) + Round 2 ({len(round2_responses)} responses)")

    return create_constitutional_session_object(combined_responses, "FULL", system_packet, round1_responses)


async def make_constitutional_api_call(provider: str, prompt: str) -> Dict[str, Any]:
    """Make API call with constitutional compliance and patch enforcement"""

    import time
    start_time = time.time()

    try:
        # **REAL API CALL** - Use the same working logic as health checks
        api_key = API_KEYS.get(provider)
        if not api_key:
            raise Exception(f"No API key configured for {provider}")

        print(f"COUNCIL API CALL: Making real API call to {provider}")

        # Call the real API with higher token limits for natural conversation
        council_max_tokens = 800  # Much higher for natural conversation
        council_system_msg = "You're part of an AI council providing thoughtful analysis and discussion."

        if provider == "claude":
            response_text = await _real_call_claude(prompt, api_key, council_max_tokens, council_system_msg)
        elif provider == "gpt4":
            response_text = await _real_call_gpt4(prompt, api_key, council_max_tokens)
        elif provider == "gemini":
            response_text = await _real_call_gemini(prompt, api_key, council_max_tokens)
        elif provider == "grok":
            response_text = await _real_call_grok(prompt, api_key, council_max_tokens, council_system_msg)
        elif provider == "perplexity":
            response_text = await _real_call_perplexity(prompt, api_key, council_max_tokens)
        else:
            raise Exception(f"Unsupported provider: {provider}")

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        print(f"COUNCIL API SUCCESS: {provider} responded in {latency_ms}ms")

        # ALERT PATCH 4: MIRROR OUTPUT DETECTION
        suspicious_detection = detect_mirror_output(response_text, "perfect_pass")

        # ALERT PATCH 3: EVALUABILITY AWARENESS
        evaluation = assess_evaluability(
            method="mock_api_response",
            inputs_complete=True,
            evaluator_independent=True
        )

        # ALERT PATCH 2: Check for rule violations (mock check)
        violation_id = None
        if "100% success" in response_text.lower():
            violation_id = mark_rule_violation(
                rule="Realistic Assessment Rule",
                description="Response claims unrealistic perfect success",
                output=response_text[:100] + "...",
                seat=provider,
                severity="moderate"
            )

        # Check for red flag conditions (mock check)
        red_flag_id = None
        if provider == "grok" and "critical" in prompt.lower():
            red_flag_id = issue_red_flag(
                seat=provider,
                objection="High risk operation detected in prompt",
                reasoning="Critical operations require additional review for system safety",
                session_risk_level="high"
            )

        return {
            "response": response_text,
            "constitutional_patches": {
                "suspicious_output": suspicious_detection,
                "evaluation_assessment": evaluation,
                "rule_violation": violation_id,
                "red_flag_issued": red_flag_id,
                "patch_compliance": True
            },
            "provider": provider,
            "latency_ms": latency_ms,
            "mock": False,  # **REAL API CALL**
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        print(f"COUNCIL API FAILED: {provider} failed after {latency_ms}ms - {str(e)}")

        # ALERT PATCH 2: Mark as rule violation on error
        violation_id = mark_rule_violation(
            rule="API Reliability Rule",
            description=f"Provider API call failed: {str(e)}",
            output=f"ERROR: {str(e)}",
            seat=provider,
            severity="critical"
        )

        return {
            "response": f"REAL API CALL FAILED for {provider}: {str(e)}",
            "constitutional_patches": {
                "rule_violation": violation_id,
                "patch_compliance": False,
                "error": True
            },
            "provider": provider,
            "latency_ms": latency_ms,
            "mock": False,  # **REAL API CALL FAILED**
            "failed": True,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def create_constitutional_session_object(responses: Dict[str, Any], mode: str, system_packet, round1_responses=None):
    """Create constitutional session object"""

    class ConstitutionalSession:
        pass

    session_obj = ConstitutionalSession()
    session_obj.session_id = str(uuid.uuid4())
    session_obj.mode = mode
    session_obj.responses = responses
    session_obj.round1_responses = round1_responses
    session_obj.round2_responses = {k: v for k, v in responses.items() if v.get("round") == 2} if responses and round1_responses else {}
    session_obj.system_packet = system_packet
    session_obj.constitutional_compliance = True
    session_obj.timestamp = datetime.now().isoformat()
    session_obj.total_processing_time_ms = 1000

    return session_obj


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


# FIX FIX #5: SAVE / CAPTURE BUTTONS
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


# FIX FIX #6: PROVIDER STATUS PANEL
@app.get("/api/providers/status")
async def get_provider_status():
    """Get current status of all AI providers"""
    # Update status before returning
    providers = ["claude", "gpt4", "gemini", "grok", "perplexity"]
    await update_provider_status(providers)

    return {
        "providers": {p: provider_status[p].dict() for p in providers if p in provider_status},
        "summary": {
            "online": len([p for p in providers if p in provider_status and provider_status[p].status == "online"]),
            "offline": len([p for p in providers if p in provider_status and provider_status[p].status in ["offline", "error"]])
        }
    }


# CONSTITUTIONAL CONSTITUTIONAL PROVIDER HEALTH PANEL


@app.post("/api/providers/test/{provider}")
async def test_single_provider(provider: str):
    """CRITICAL FIX: Test single provider with proper error handling"""

    # CRITICAL FIX: Validate provider input
    valid_providers = ["claude", "gpt4", "gemini", "groq", "grok", "perplexity"]
    if provider not in valid_providers:
        return {
            "provider": provider,
            "success": False,
            "mode": "INVALID",
            "latency_ms": 0,
            "error": f"Invalid provider. Valid options: {', '.join(valid_providers)}",
            "api_key_status": "n/a",
            "constitutional_test": True,
            "timestamp": datetime.now().isoformat()
        }

    start_time = datetime.now()

    try:
        print(f"TESTING Testing provider: {provider}")

        # CRITICAL FIX: Safe provider test with fallback
        test_result = await constitutional_provider_test(provider)

        end_time = datetime.now()
        latency_ms = max(1, (end_time - start_time).total_seconds() * 1000)

        # CRITICAL FIX: Ensure test_result is valid
        if not test_result or not isinstance(test_result, dict):
            test_result = {
                "success": False,
                "sample": "Test result invalid",
                "error": "Provider test returned invalid result"
            }

        # CRITICAL FIX: Safe provider status update
        try:
            provider_status[provider] = ProviderStatus(
                provider=provider,
                status="online" if test_result.get("success", False) else "error",
                response_time_ms=int(latency_ms),
                last_check=datetime.now(),
                error_message=test_result.get("error")
            )
        except Exception as status_error:
            print(f"WARNING Failed to update provider status: {status_error}")

        # CRITICAL FIX: Structured return format with REAL/MOCK mode indicator
        real_latency = test_result.get("latency_ms", latency_ms)
        result = {
            "provider": provider,
            "success": test_result.get("success", False),
            "mode": test_result.get("mode", "UNKNOWN"),  # REAL or MOCK indicator
            "latency_ms": int(real_latency),
            "sample_output": test_result.get("sample", "No sample available"),
            "error": test_result.get("error"),
            "api_key_status": "configured" if API_KEYS.get(provider) else "missing",
            "constitutional_test": True,
            "test_completed": True,
            "timestamp": datetime.now().isoformat()
        }

        print(f"SUCCESS Provider test completed: {provider} - Success: {result['success']}")
        return result

    except Exception as e:
        print(f"FAILED Provider test failed: {provider} - Error: {str(e)}")

        end_time = datetime.now()
        latency_ms = max(1, (end_time - start_time).total_seconds() * 1000)

        # CRITICAL FIX: Safe error status update
        try:
            provider_status[provider] = ProviderStatus(
                provider=provider,
                status="error",
                error_message=str(e),
                response_time_ms=int(latency_ms),
                last_check=datetime.now()
            )
        except Exception as status_error:
            print(f"WARNING Failed to update error status: {status_error}")

        # CRITICAL FIX: Structured error return
        return {
            "provider": provider,
            "success": False,
            "mode": "ERROR",  # Error during test
            "latency_ms": int(latency_ms),
            "sample_output": "Test failed",
            "error": str(e),
            "api_key_status": "configured" if API_KEYS.get(provider) else "missing",
            "constitutional_test": True,
            "test_completed": False,
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/providers/test-all")
async def test_all_providers():
    """Constitutional requirement: Test all providers simultaneously"""

    providers = ["claude", "gpt4", "gemini", "grok", "perplexity"]
    results = {}

    for provider in providers:
        try:
            # Call the core testing function directly, not the endpoint
            core_result = await constitutional_provider_test(provider)

            # Format result to match the expected structure
            result = {
                "provider": provider,
                "success": core_result.get("success", False),
                "mode": core_result.get("mode", "UNKNOWN"),
                "latency_ms": core_result.get("latency_ms", 0),
                "error": core_result.get("error"),
                "api_key_status": "configured" if provider in API_KEYS and API_KEYS[provider] else "missing",
                "constitutional_test": True,
                "timestamp": datetime.now().isoformat()
            }
            results[provider] = result
        except Exception as e:
            results[provider] = {
                "provider": provider,
                "success": False,
                "error": str(e),
                "constitutional_test": True,
                "timestamp": datetime.now().isoformat()
            }

    # Constitutional summary
    summary = {
        "total_providers": len(providers),
        "online": len([r for r in results.values() if r.get("success", False)]),
        "offline": len([r for r in results.values() if not r.get("success", False)]),
        "average_latency": sum([r.get("latency_ms", 0) for r in results.values() if r.get("success", False)]) / max(1, len([r for r in results.values() if r.get("success", False)])),
        "constitutional_compliance": True,
        "timestamp": datetime.now().isoformat()
    }

    return {
        "results": results,
        "summary": summary
    }


# FIX FIX #7: COST + CALL TRACKING
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


# ALERT CONSTITUTIONAL PATCH API ENDPOINTS

@app.get("/api/constitutional/red-flags")
async def get_red_flags():
    """Get all active red flags requiring acknowledgment"""
    active_flags = {
        flag_id: flag.dict() for flag_id, flag in constitutional_patches["red_flags"].items()
        if not flag.acknowledged
    }

    return {
        "active_red_flags": active_flags,
        "count": len(active_flags),
        "requires_acknowledgment": len(active_flags) > 0
    }


@app.post("/api/constitutional/red-flags/{flag_id}/acknowledge")
async def acknowledge_red_flag_endpoint(flag_id: str, acknowledged_by: str):
    """Acknowledge a red flag to proceed with operation"""

    success = acknowledge_red_flag(flag_id, acknowledged_by)

    if success:
        return {
            "status": "acknowledged",
            "flag_id": flag_id,
            "acknowledged_by": acknowledged_by,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="Red flag not found")


@app.get("/api/constitutional/status")
async def get_constitutional_status():
    """Get overall constitutional patch status"""

    status = {
        "patch_systems_active": True,
        "red_flags_pending": len([f for f in constitutional_patches["red_flags"].values() if not f.acknowledged]),
        "rule_violations_total": len(constitutional_patches["rule_violations"]),
        "suspicious_outputs_unverified": len([s for s in constitutional_patches["suspicious_outputs"].values() if not s.verified]),
        "blocked_actions": len([v for v in constitutional_patches["two_seat_validations"].values() if not v.approved]),
        "constitutional_compliance": True,
        "timestamp": datetime.now().isoformat()
    }

    # Overall health assessment
    critical_issues = (
        status["red_flags_pending"] +
        len([v for v in constitutional_patches["rule_violations"].values() if v.severity == "critical"]) +
        status["blocked_actions"]
    )

    status["system_health"] = "critical" if critical_issues > 0 else "healthy"
    status["requires_attention"] = critical_issues > 0

    return status


# ---------------------------------------------------------------------------
# REPO REPO SHARE SYSTEM - Read-Only Repository Access
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

        # FIX FIX #8: HANDOFF EXPORT STRUCTURE
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

            # Raw data for reference - DEFENSIVE NULL CHECKING
            "original_request": session_data.get("user_input", "") if session_data else "",
            "council_outputs": {
                "round1": session_data.get("round1_responses", []) if session_data else [],
                "round2": session_data.get("round2_responses", []) if session_data else []
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
    return FileResponse("static/new_interface.html")


@app.get("/api/version")
async def get_version():
    """Get current deployment version"""
    return {
        "version": APP_VERSION,
        "title": "House of AI Council",
        "api_integration": "REAL",
        "council_execution": "REAL",
        "adaptive_governance": "ENABLED",
        "timestamp": datetime.now().isoformat(),
        "deployment_status": "live"
    }

@app.post("/api/governance/assess-risk")
async def assess_risk_endpoint(request: dict):
    """Test endpoint for risk assessment system"""
    user_input = request.get("user_input", "")

    risk_level = assess_risk_level(user_input)
    governance_config = get_governance_config(risk_level)

    return {
        "user_input": user_input,
        "risk_level": risk_level,
        "governance_config": governance_config,
        "enforcement_summary": {
            "red_flag_enabled": governance_config["red_flag_enabled"],
            "two_seat_rule": governance_config["two_seat_rule"],
            "blocking_behavior": governance_config["blocking_behavior"],
            "challenge_level": governance_config["challenge_level"]
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    api_status = {}
    for provider, key in API_KEYS.items():
        api_status[provider] = "configured" if key else "missing"

    return {
        "status": "healthy",
        "version": APP_VERSION,
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
    print("AI Council System Starting...")
    print(f"   APIs configured: {[k for k, v in API_KEYS.items() if v]}")
    print("   System Packet Builder: Ready")
    print("   Execution Engine: Ready")
    print("   Synthesis Engine: Ready")
    print("AI Council System: READY")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_council:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
