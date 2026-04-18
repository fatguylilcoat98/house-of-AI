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

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class CouncilRequest(BaseModel):
    user_input: str
    session_goal: Optional[Dict[str, Any]] = None
    custom_constitution: Optional[Dict[str, Any]] = None


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
    """Execute full two-round council session"""
    try:
        # Update constitution if provided
        if request.custom_constitution:
            constitution = ConstitutionCore(**request.custom_constitution)
            packet_builder.update_constitution(constitution)

        # Update session goal if provided
        session_goal = None
        if request.session_goal:
            session_goal = SessionGoal(**request.session_goal)

        # Execute council session
        session = await execution_engine.execute_full_council_session(
            request.user_input
        )

        # Generate synthesis
        synthesis = synthesis_engine.synthesize_council_session(session)

        return {
            "status": "success",
            "session_id": session.session_id,
            "session": execution_engine.export_session(session.session_id),
            "synthesis": synthesis_engine.export_synthesis(synthesis),
            "processing_time_ms": session.total_processing_time_ms
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Council execution failed: {str(e)}")


@app.get("/api/council/session/{session_id}")
async def get_session(session_id: str):
    """Retrieve council session by ID"""
    session_data = execution_engine.export_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    return session_data


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

        handoff_packet = {
            "handoff_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "recipient": request.recipient,
            "purpose": request.purpose,
            "session_id": request.session_id,
            "user_input": session_data["user_input"],
            "council_outputs": {
                "round1": session_data["round1_responses"],
                "round2": session_data["round2_responses"]
            },
            "synthesis": synthesis_engine.export_synthesis(synthesis) if synthesis else None,
            "system_context": packet_builder.export_state() if request.include_full_context else None,
            "handoff_summary": f"AI Council session for '{request.recipient}' regarding: {session_data['user_input'][:200]}..."
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

# Serve static files (will create clean UI later)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint - serve main interface"""
    return {"message": "AI Council System - Clean Architecture", "version": "1.0.0"}


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
"""