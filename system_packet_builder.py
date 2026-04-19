"""
System Packet Builder - AI Council Core Component
Creates comprehensive context packets for council members

Built by Christopher Hughes & The Good Neighbor Guard
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from dataclasses import dataclass, asdict


@dataclass
class ConstitutionCore:
    """User's core values and operational rules"""
    core_values: List[str]
    decision_principles: List[str]
    constraints: List[str]
    priorities: List[str]

    @classmethod
    def default(cls):
        return cls(
            core_values=[
                "Good Neighbor Guard ethos - build for others' benefit",
                "Truth and transparency in all outputs",
                "Respect user autonomy and choice",
                "House of AI is the council chamber - not a build system",
                "Claude Code remains the only build system",
                "Sole Carrier Rule: Models do not share native memory",
                "Minimize harm, maximize utility"
            ],
            decision_principles=[
                "Evidence-based reasoning - VERIFIED/OPINION/UNKNOWN classification",
                "Truth over agreement - challenge incorrect claims",
                "Preserve disagreement - no fake consensus",
                "Flag assumptions clearly - do not guess",
                "Stay in assigned lanes - respect role boundaries",
                "Independent reasoning - no cross-seat assumptions"
            ],
            constraints=[
                "SOLE CARRIER RULE: Only session packet information is valid",
                "VOICE INTEGRITY: Speak only for yourself, no simulation",
                "NO ASSUMPTION: Do not assume other seats verified anything",
                "CLAIM PROVENANCE: Tag as MEASURED/INFERRED/ASSUMED/GENERATED",
                "REPO VISIBILITY: Only shared repo context is valid",
                "UNCERTAINTY DEFAULT: If unclear, say UNKNOWN"
            ],
            priorities=[
                "Truth before agreement",
                "Safety before flow",
                "Clarity before speed",
                "Verification before trust",
                "Council escalation for significant decisions"
            ]
        )


@dataclass
class ActiveSystemState:
    """Current project context and state"""
    project_name: str
    current_phase: str
    goals: List[str]
    constraints: List[str]
    context_summary: str
    key_decisions: List[Dict[str, Any]]
    open_questions: List[str]
    last_updated: datetime

    @classmethod
    def default(cls):
        return cls(
            project_name="New Council Session",
            current_phase="initial",
            goals=["Provide coordinated AI council guidance"],
            constraints=["Standard operational constraints"],
            context_summary="Fresh council session starting",
            key_decisions=[],
            open_questions=[],
            last_updated=datetime.now()
        )


@dataclass
class SessionGoal:
    """What we're trying to achieve in this session"""
    primary_objective: str
    success_criteria: List[str]
    deliverables: List[str]
    timeframe: Optional[str]
    stakeholders: List[str]

    @classmethod
    def from_input(cls, user_input: str):
        # Basic goal extraction - can be enhanced with NLP
        return cls(
            primary_objective=f"Address user request: {user_input[:100]}...",
            success_criteria=["Provide comprehensive council response"],
            deliverables=["Council analysis", "Recommendations", "Next steps"],
            timeframe=None,
            stakeholders=["User"]
        )


@dataclass
class SystemPacket:
    """Complete context packet for AI council members"""
    packet_id: str
    timestamp: datetime
    constitution: ConstitutionCore
    system_state: ActiveSystemState
    session_goal: SessionGoal
    user_input: str
    round_number: int
    previous_outputs: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_prompt(self, ai_role: str) -> str:
        """Convert packet to formatted prompt for specific AI role"""

        role_instructions = {
            "claude": "You are Claude, focused on ARCHITECTURE & SYSTEMS DESIGN. Analyze structural decisions, technical approaches, and system-level considerations.",
            "gpt": "You are GPT-4, focused on STRUCTURE & IMPLEMENTATION. Analyze implementation details, code organization, and development approaches.",
            "gemini": "You are Gemini, focused on USER EXPERIENCE & INTERFACE. Analyze usability, design decisions, and user interaction patterns.",
            "grok": "You are Grok, focused on STRESS TESTING & EDGE CASES. Analyze potential failures, edge cases, and system limits."
        }

        packet_prompt = f"""
=== AI COUNCIL SYSTEM PACKET ===
Packet ID: {self.packet_id}
Timestamp: {self.timestamp.isoformat()}
Round: {self.round_number}

{role_instructions.get(ai_role, "You are an AI council member.")}

=== CONSTITUTION CORE ===
Core Values:
{chr(10).join(f"• {v}" for v in self.constitution.core_values)}

Decision Principles:
{chr(10).join(f"• {p}" for p in self.constitution.decision_principles)}

Constraints:
{chr(10).join(f"• {c}" for c in self.constitution.constraints)}

Priorities:
{chr(10).join(f"• {p}" for p in self.constitution.priorities)}

=== ACTIVE SYSTEM STATE ===
Project: {self.system_state.project_name}
Phase: {self.system_state.current_phase}
Goals: {', '.join(self.system_state.goals)}
Context: {self.system_state.context_summary}

Open Questions:
{chr(10).join(f"• {q}" for q in self.system_state.open_questions)}

=== SESSION GOAL ===
Primary Objective: {self.session_goal.primary_objective}
Success Criteria: {', '.join(self.session_goal.success_criteria)}
Deliverables: {', '.join(self.session_goal.deliverables)}

=== USER INPUT ===
{self.user_input}
"""

        if self.round_number == 2 and self.previous_outputs:
            packet_prompt += f"""
=== ROUND 1 OUTPUTS FOR CROSS-REVIEW ===
{json.dumps(self.previous_outputs, indent=2)}

CROSS-REVIEW INSTRUCTIONS:
1. Review all Round 1 outputs from council members
2. Identify agreements, conflicts, and gaps
3. Provide your perspective on the other members' analysis
4. Flag any assumptions or claims that need verification
5. Suggest synthesis opportunities or irreconcilable differences
"""

        packet_prompt += """

RESPONSE REQUIREMENTS:
1. Tag claims with provenance: [MEASURED], [INFERRED], [ASSUMED], [GENERATED]
2. Maintain your distinct voice - do NOT merge with other perspectives
3. Be specific and actionable
4. Flag uncertainties and assumptions clearly
5. Consider the sole carrier rule - make your response complete and self-contained

Your response:
"""

        return packet_prompt


class SystemPacketBuilder:
    """Builds system packets for council members"""

    def __init__(self):
        self.constitution = ConstitutionCore.default()
        self.system_state = ActiveSystemState.default()

    def update_constitution(self, constitution: ConstitutionCore):
        """Update the constitution core"""
        self.constitution = constitution

    def update_system_state(self, system_state: ActiveSystemState):
        """Update the active system state"""
        self.system_state = system_state
        self.system_state.last_updated = datetime.now()

    def build_packet(
        self,
        user_input: str,
        round_number: int = 1,
        previous_outputs: Optional[Dict[str, Any]] = None,
        custom_goal: Optional[SessionGoal] = None,
        repo_context: Optional[Dict[str, Any]] = None
    ) -> SystemPacket:
        """Build a complete constitutional system packet"""

        # CONSTITUTIONAL REQUIREMENT: Every packet must include all core components
        if not user_input.strip():
            raise ValueError("CONSTITUTIONAL VIOLATION: No user prompt provided")

        if not self.constitution:
            raise ValueError("CONSTITUTIONAL VIOLATION: No Constitution Core loaded")

        if not self.system_state:
            raise ValueError("CONSTITUTIONAL VIOLATION: No Active System State")

        session_goal = custom_goal or SessionGoal.from_input(user_input)

        # Build constitutional metadata
        constitutional_metadata = {
            "builder_version": "1.0.0-CONSTITUTIONAL",
            "packet_size": len(user_input),
            "constitutional_compliance": True,
            "sole_carrier_rule_active": True,
            "timestamp": datetime.now().isoformat()
        }

        # Add repo analysis requirements if repo context present
        if repo_context:
            constitutional_metadata.update({
                "repo_context_included": True,
                "repo_analysis_injection": "You are analyzing shared repository context. Do not assume missing files exist. Do not infer behavior outside provided code. Flag unknowns instead of guessing.",
                "repo_metadata": repo_context.get("repo_share_metadata", {}),
                "read_only_status": True
            })

        packet = SystemPacket(
            packet_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            constitution=self.constitution,
            system_state=self.system_state,
            session_goal=session_goal,
            user_input=user_input,
            round_number=round_number,
            previous_outputs=previous_outputs,
            metadata=constitutional_metadata
        )

        # CONSTITUTIONAL VALIDATION: Ensure packet completeness
        self._validate_constitutional_packet(packet, repo_context)

        return packet

    def _validate_constitutional_packet(self, packet: SystemPacket, repo_context: Optional[Dict[str, Any]] = None):
        """Validate packet meets constitutional requirements"""

        required_components = [
            ("Constitution Core", packet.constitution),
            ("Active System State", packet.system_state),
            ("Session Goal", packet.session_goal),
            ("User Prompt", packet.user_input)
        ]

        missing = [name for name, component in required_components if not component]

        if missing:
            raise ValueError(f"CONSTITUTIONAL VIOLATION: Missing required components: {', '.join(missing)}")

        # Validate repo context if present
        if repo_context and not repo_context.get("repo_share_metadata"):
            raise ValueError("CONSTITUTIONAL VIOLATION: Repo context provided without proper metadata")

    def add_repo_context(self, repo_context: Dict[str, Any]):
        """Add repository context to the next packet build"""
        # This method referenced in main_council.py
        self._pending_repo_context = repo_context

    def export_state(self) -> Dict[str, Any]:
        """Export current builder state"""
        return {
            "constitution": asdict(self.constitution),
            "system_state": asdict(self.system_state),
            "exported_at": datetime.now().isoformat()
        }

    def import_state(self, state_data: Dict[str, Any]):
        """Import builder state"""
        if "constitution" in state_data:
            self.constitution = ConstitutionCore(**state_data["constitution"])
        if "system_state" in state_data:
            state_data["system_state"]["last_updated"] = datetime.fromisoformat(
                state_data["system_state"]["last_updated"]
            )
            self.system_state = ActiveSystemState(**state_data["system_state"])


# Example usage and testing
if __name__ == "__main__":
    builder = SystemPacketBuilder()

    # Test packet creation
    packet = builder.build_packet("Help me design a new authentication system")

    print("=== CLAUDE PROMPT ===")
    print(packet.to_prompt("claude"))

    print("\n=== GROK PROMPT ===")
    print(packet.to_prompt("grok"))

    # Test state export
    print("\n=== EXPORTED STATE ===")
    print(json.dumps(builder.export_state(), indent=2, default=str))