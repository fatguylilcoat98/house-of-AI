"""
Builder Instance Manager - Dual Claude Code Instance Coordination
Tracks desktop and phone Claude Code instances independently

Built by Christopher Hughes & The Good Neighbor Guard
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class InstanceStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    NEEDS_HANDOFF = "needs_handoff"
    WAITING_HANDOFF = "waiting_handoff"
    OFFLINE = "offline"


class HandoffType(Enum):
    CONTEXT_TRANSFER = "context_transfer"
    TASK_DELEGATION = "task_delegation"
    EMERGENCY_HANDOFF = "emergency_handoff"
    SESSION_SWITCH = "session_switch"
    VERIFICATION_REQUEST = "verification_request"


@dataclass
class BuilderInstance:
    """Represents a single Claude Code builder instance"""
    instance_id: str
    instance_name: str  # "Desktop", "Phone", etc.
    device_type: str
    assigned_project: str
    current_task: str
    last_verified_action: str
    branch_workspace: str
    status: InstanceStatus
    last_active: datetime
    session_id: Optional[str] = None
    current_directory: Optional[str] = None
    git_status: Optional[str] = None
    open_files: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.open_files is None:
            self.open_files = []
        if self.metadata is None:
            self.metadata = {}

    def update_status(self, new_status: InstanceStatus, reason: str = ""):
        """Update instance status with timestamp"""
        self.status = new_status
        self.last_active = datetime.now()
        if reason:
            self.metadata["status_change_reason"] = reason
            self.metadata["status_changed_at"] = datetime.now().isoformat()

    def update_task(self, new_task: str, workspace: str = None):
        """Update current task and workspace"""
        self.current_task = new_task
        if workspace:
            self.branch_workspace = workspace
        self.last_active = datetime.now()

    def verify_action(self, action: str):
        """Mark an action as verified"""
        self.last_verified_action = action
        self.last_active = datetime.now()
        self.metadata["last_verification"] = {
            "action": action,
            "verified_at": datetime.now().isoformat()
        }


@dataclass
class InstanceHandoff:
    """Handoff package between builder instances"""
    handoff_id: str
    handoff_type: HandoffType
    from_instance: str
    to_instance: str
    project_context: str
    task_description: str
    current_state: Dict[str, Any]
    verification_requirements: List[str]
    git_context: Dict[str, Any]
    file_context: List[Dict[str, Any]]
    session_data: Optional[Dict[str, Any]]
    instructions: str
    priority: str  # "low", "normal", "high", "critical"
    deadline: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime] = None
    handoff_notes: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def complete_handoff(self, completion_notes: str = ""):
        """Mark handoff as completed"""
        self.completed_at = datetime.now()
        self.handoff_notes = completion_notes


class BuilderInstanceManager:
    """Manages multiple Claude Code builder instances"""

    def __init__(self, storage_path: str = "./instance_data/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        self.instances: Dict[str, BuilderInstance] = {}
        self.handoffs: Dict[str, InstanceHandoff] = {}
        self.handoff_history: List[InstanceHandoff] = []

        # Multi-instance builder rules
        self.builder_rules = {
            "no_shared_context": True,
            "explicit_handoff_required": True,
            "verify_before_assume": True,
            "document_all_transfers": True
        }

        # Load existing instances
        self._load_instances()

    def register_instance(
        self,
        instance_name: str,
        device_type: str,
        initial_project: str = "Unassigned"
    ) -> str:
        """Register a new builder instance"""

        instance_id = f"builder_{instance_name.lower()}_{int(datetime.now().timestamp())}"

        instance = BuilderInstance(
            instance_id=instance_id,
            instance_name=instance_name,
            device_type=device_type,
            assigned_project=initial_project,
            current_task="Idle",
            last_verified_action="Instance registered",
            branch_workspace="main",
            status=InstanceStatus.ACTIVE,
            last_active=datetime.now(),
            metadata={
                "registered_at": datetime.now().isoformat(),
                "registration_session": str(uuid.uuid4())
            }
        )

        self.instances[instance_id] = instance
        self._save_instances()
        return instance_id

    def update_instance_status(
        self,
        instance_id: str,
        status: InstanceStatus,
        task: str = None,
        workspace: str = None,
        verified_action: str = None
    ):
        """Update instance status and context"""

        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not found")

        instance = self.instances[instance_id]
        instance.update_status(status)

        if task:
            instance.update_task(task, workspace)
        if verified_action:
            instance.verify_action(verified_action)

        self._save_instances()

    def create_handoff(
        self,
        from_instance_id: str,
        to_instance_id: str,
        handoff_type: HandoffType,
        project_context: str,
        task_description: str,
        current_state: Dict[str, Any],
        instructions: str,
        priority: str = "normal",
        deadline: Optional[datetime] = None
    ) -> str:
        """Create handoff between instances"""

        # Verify both instances exist
        if from_instance_id not in self.instances:
            raise ValueError(f"Source instance {from_instance_id} not found")
        if to_instance_id not in self.instances:
            raise ValueError(f"Target instance {to_instance_id} not found")

        from_instance = self.instances[from_instance_id]
        to_instance = self.instances[to_instance_id]

        # Create handoff package
        handoff_id = str(uuid.uuid4())

        # Extract git and file context from source instance
        git_context = {
            "current_branch": from_instance.branch_workspace,
            "last_commit": current_state.get("last_commit", "unknown"),
            "uncommitted_changes": current_state.get("uncommitted_changes", False),
            "git_status": from_instance.git_status
        }

        file_context = []
        for file_path in from_instance.open_files:
            file_context.append({
                "path": file_path,
                "last_modified": current_state.get(f"file_modified_{file_path}", "unknown"),
                "change_status": current_state.get(f"file_status_{file_path}", "unknown")
            })

        handoff = InstanceHandoff(
            handoff_id=handoff_id,
            handoff_type=handoff_type,
            from_instance=from_instance_id,
            to_instance=to_instance_id,
            project_context=project_context,
            task_description=task_description,
            current_state=current_state,
            verification_requirements=[
                f"Verify {from_instance.last_verified_action}",
                f"Confirm context: {project_context}",
                f"Validate task: {task_description}"
            ],
            git_context=git_context,
            file_context=file_context,
            session_data=current_state.get("session_data"),
            instructions=instructions,
            priority=priority,
            deadline=deadline,
            created_at=datetime.now()
        )

        # Update instance statuses
        from_instance.update_status(InstanceStatus.NEEDS_HANDOFF, "Handoff created")
        to_instance.update_status(InstanceStatus.WAITING_HANDOFF, "Handoff pending")

        self.handoffs[handoff_id] = handoff
        self._save_instances()
        self._save_handoffs()

        return handoff_id

    def accept_handoff(
        self,
        handoff_id: str,
        accepting_instance_id: str,
        verification_notes: str = ""
    ):
        """Accept and complete a handoff"""

        if handoff_id not in self.handoffs:
            raise ValueError(f"Handoff {handoff_id} not found")

        handoff = self.handoffs[handoff_id]

        if handoff.to_instance != accepting_instance_id:
            raise ValueError(f"Handoff not intended for instance {accepting_instance_id}")

        # Complete handoff
        handoff.complete_handoff(verification_notes)

        # Update instance statuses
        from_instance = self.instances[handoff.from_instance]
        to_instance = self.instances[handoff.to_instance]

        from_instance.update_status(InstanceStatus.PAUSED, "Handoff completed")

        # Transfer context to receiving instance
        to_instance.assigned_project = handoff.project_context
        to_instance.current_task = handoff.task_description
        to_instance.branch_workspace = handoff.git_context["current_branch"]
        to_instance.update_status(InstanceStatus.ACTIVE, "Handoff accepted")
        to_instance.verify_action(f"Handoff accepted: {handoff.task_description}")

        # Move to history
        self.handoff_history.append(handoff)
        del self.handoffs[handoff_id]

        self._save_instances()
        self._save_handoffs()

    def get_instance_status(self, instance_id: str) -> Optional[BuilderInstance]:
        """Get current status of an instance"""
        return self.instances.get(instance_id)

    def get_all_instances(self) -> Dict[str, BuilderInstance]:
        """Get all registered instances"""
        return self.instances.copy()

    def get_pending_handoffs(self, instance_id: str = None) -> List[InstanceHandoff]:
        """Get pending handoffs, optionally filtered by instance"""
        handoffs = list(self.handoffs.values())

        if instance_id:
            handoffs = [h for h in handoffs
                       if h.to_instance == instance_id or h.from_instance == instance_id]

        return handoffs

    def enforce_builder_rules(self, operation: str, context: Dict[str, Any]) -> bool:
        """Enforce multi-instance builder rules"""

        # No shared context assumption
        if self.builder_rules["no_shared_context"]:
            if "assumes_other_context" in context:
                return False

        # Explicit handoff required
        if self.builder_rules["explicit_handoff_required"]:
            if operation == "cross_instance_reference" and "handoff_id" not in context:
                return False

        # Verify before assume
        if self.builder_rules["verify_before_assume"]:
            if "unverified_assumption" in context:
                return False

        return True

    def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""

        active_instances = [i for i in self.instances.values()
                          if i.status == InstanceStatus.ACTIVE]
        pending_handoffs = list(self.handoffs.values())

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_instances": len(self.instances),
            "active_instances": len(active_instances),
            "pending_handoffs": len(pending_handoffs),
            "instance_details": {
                instance_id: {
                    "name": instance.instance_name,
                    "project": instance.assigned_project,
                    "task": instance.current_task,
                    "status": instance.status.value,
                    "last_active": instance.last_active.isoformat(),
                    "workspace": instance.branch_workspace
                }
                for instance_id, instance in self.instances.items()
            },
            "handoff_summary": [
                {
                    "handoff_id": handoff.handoff_id,
                    "type": handoff.handoff_type.value,
                    "from": self.instances[handoff.from_instance].instance_name,
                    "to": self.instances[handoff.to_instance].instance_name,
                    "project": handoff.project_context,
                    "priority": handoff.priority,
                    "created": handoff.created_at.isoformat()
                }
                for handoff in pending_handoffs
            ],
            "builder_rules": self.builder_rules
        }

        return report

    def _save_instances(self):
        """Save instances to storage"""
        instances_data = {
            instance_id: asdict(instance)
            for instance_id, instance in self.instances.items()
        }

        with open(self.storage_path / "instances.json", "w") as f:
            json.dump(instances_data, f, indent=2, default=str)

    def _save_handoffs(self):
        """Save handoffs to storage"""
        handoffs_data = {
            handoff_id: asdict(handoff)
            for handoff_id, handoff in self.handoffs.items()
        }

        with open(self.storage_path / "handoffs.json", "w") as f:
            json.dump(handoffs_data, f, indent=2, default=str)

    def _load_instances(self):
        """Load instances from storage"""
        instances_file = self.storage_path / "instances.json"
        if instances_file.exists():
            try:
                with open(instances_file, "r") as f:
                    data = json.load(f)

                for instance_id, instance_data in data.items():
                    # Convert datetime strings back to datetime objects
                    instance_data["last_active"] = datetime.fromisoformat(
                        instance_data["last_active"]
                    )
                    instance_data["status"] = InstanceStatus(instance_data["status"])

                    self.instances[instance_id] = BuilderInstance(**instance_data)
            except Exception as e:
                print(f"Error loading instances: {e}")


# Example usage and testing
if __name__ == "__main__":
    manager = BuilderInstanceManager()

    # Register desktop and phone instances
    desktop_id = manager.register_instance("Desktop", "windows_desktop", "AI Council System")
    phone_id = manager.register_instance("Phone", "mobile_android", "Authentication Design")

    # Update desktop status
    manager.update_instance_status(
        desktop_id,
        InstanceStatus.ACTIVE,
        task="Building council synthesis engine",
        workspace="feature/synthesis-engine",
        verified_action="Synthesis engine tests passing"
    )

    # Create handoff from desktop to phone
    handoff_id = manager.create_handoff(
        from_instance_id=desktop_id,
        to_instance_id=phone_id,
        handoff_type=HandoffType.TASK_DELEGATION,
        project_context="AI Council System - Synthesis Engine",
        task_description="Review synthesis engine implementation and test edge cases",
        current_state={
            "last_commit": "abc123: Add synthesis engine",
            "uncommitted_changes": False,
            "open_files": ["synthesis_engine.py", "test_synthesis.py"],
            "test_status": "all_passing"
        },
        instructions="Please review the synthesis engine implementation for edge cases and add any missing error handling",
        priority="high"
    )

    # Generate status report
    report = manager.generate_status_report()
    print(json.dumps(report, indent=2))
"""