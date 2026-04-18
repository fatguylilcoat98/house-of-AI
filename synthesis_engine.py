"""
Synthesis Engine - AI Council Analysis & Coordination
Analyzes council responses without merging voices, preserves distinct perspectives

Built by Christopher Hughes & The Good Neighbor Guard
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from council_execution_engine import CouncilSession, AIResponse, AIProvider


class ClaimProvenance(Enum):
    MEASURED = "MEASURED"
    INFERRED = "INFERRED"
    ASSUMED = "ASSUMED"
    GENERATED = "GENERATED"


class AgreementLevel(Enum):
    FULL_AGREEMENT = "full_agreement"
    PARTIAL_AGREEMENT = "partial_agreement"
    MINOR_CONFLICT = "minor_conflict"
    MAJOR_CONFLICT = "major_conflict"
    NO_OVERLAP = "no_overlap"


@dataclass
class ProvenanceClaim:
    """Tagged claim with provenance information"""
    claim: str
    provenance: ClaimProvenance
    confidence: float
    source_provider: AIProvider
    source_round: int


@dataclass
class Agreement:
    """Identified agreement between council members"""
    topic: str
    agreement_level: AgreementLevel
    participating_providers: List[AIProvider]
    consensus_statement: str
    supporting_evidence: List[str]
    provenance_breakdown: Dict[ClaimProvenance, int]


@dataclass
class Conflict:
    """Identified conflict between council members"""
    topic: str
    conflict_type: str  # "approach", "assumption", "conclusion", "priority"
    positions: Dict[AIProvider, str]
    irreconcilable: bool
    potential_resolution: Optional[str]


@dataclass
class SynthesisResult:
    """Complete synthesis analysis preserving all voices"""
    session_id: str
    synthesis_timestamp: datetime
    original_outputs: Dict[AIProvider, Dict[int, str]]  # round -> response
    provenance_analysis: Dict[AIProvider, List[ProvenanceClaim]]
    agreements: List[Agreement]
    conflicts: List[Conflict]
    key_insights: List[str]
    action_recommendations: List[str]
    knowledge_gaps: List[str]
    next_questions: List[str]
    council_summary: str  # Brief overview without merging voices


class SynthesisEngine:
    """Analyzes council outputs and identifies patterns without merging voices"""

    def __init__(self):
        self.provenance_patterns = {
            ClaimProvenance.MEASURED: [
                r'\[MEASURED\]',
                r'according to data',
                r'measurements show',
                r'statistics indicate',
                r'research demonstrates'
            ],
            ClaimProvenance.INFERRED: [
                r'\[INFERRED\]',
                r'this suggests',
                r'we can conclude',
                r'this implies',
                r'reasoning indicates'
            ],
            ClaimProvenance.ASSUMED: [
                r'\[ASSUMED\]',
                r'assuming that',
                r'if we assume',
                r'presumes that',
                r'taking for granted'
            ],
            ClaimProvenance.GENERATED: [
                r'\[GENERATED\]',
                r'hypothetically',
                r'imagine if',
                r'conceptually',
                r'as an example'
            ]
        }

    def synthesize_council_session(self, session: CouncilSession) -> SynthesisResult:
        """Synthesize complete council session preserving all voices"""

        # Extract original outputs
        original_outputs = self._extract_original_outputs(session)

        # Analyze provenance claims
        provenance_analysis = self._analyze_provenance(session)

        # Identify agreements
        agreements = self._identify_agreements(session)

        # Identify conflicts
        conflicts = self._identify_conflicts(session)

        # Extract insights and recommendations
        key_insights = self._extract_insights(session)
        action_recommendations = self._extract_recommendations(session)
        knowledge_gaps = self._identify_knowledge_gaps(session)
        next_questions = self._generate_next_questions(session)

        # Generate summary without merging voices
        council_summary = self._generate_council_summary(
            session, agreements, conflicts, key_insights
        )

        return SynthesisResult(
            session_id=session.session_id,
            synthesis_timestamp=datetime.now(),
            original_outputs=original_outputs,
            provenance_analysis=provenance_analysis,
            agreements=agreements,
            conflicts=conflicts,
            key_insights=key_insights,
            action_recommendations=action_recommendations,
            knowledge_gaps=knowledge_gaps,
            next_questions=next_questions,
            council_summary=council_summary
        )

    def _extract_original_outputs(self, session: CouncilSession) -> Dict[AIProvider, Dict[int, str]]:
        """Extract and preserve original outputs by provider and round"""
        outputs = {}

        for provider, response in session.round1_responses.items():
            if provider not in outputs:
                outputs[provider] = {}
            outputs[provider][1] = response.response_text

        for provider, response in session.round2_responses.items():
            if provider not in outputs:
                outputs[provider] = {}
            outputs[provider][2] = response.response_text

        return outputs

    def _analyze_provenance(self, session: CouncilSession) -> Dict[AIProvider, List[ProvenanceClaim]]:
        """Analyze provenance claims in each response"""
        analysis = {}

        all_responses = [
            (provider, 1, response) for provider, response in session.round1_responses.items()
        ] + [
            (provider, 2, response) for provider, response in session.round2_responses.items()
        ]

        for provider, round_num, response in all_responses:
            if response.error:
                continue

            claims = []
            text = response.response_text

            # Extract claims with explicit provenance tags
            for provenance, patterns in self.provenance_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        # Extract surrounding context as claim
                        start = max(0, match.start() - 100)
                        end = min(len(text), match.end() + 100)
                        claim_text = text[start:end].strip()

                        claims.append(ProvenanceClaim(
                            claim=claim_text,
                            provenance=provenance,
                            confidence=0.8,  # Could be enhanced with ML
                            source_provider=provider,
                            source_round=round_num
                        ))

            analysis[provider] = claims

        return analysis

    def _identify_agreements(self, session: CouncilSession) -> List[Agreement]:
        """Identify agreements between council members"""
        agreements = []

        # Simple agreement detection based on common themes
        # This could be enhanced with semantic similarity analysis

        responses = {}
        for provider, response in session.round1_responses.items():
            if not response.error:
                responses[provider] = response.response_text

        # Look for common themes/keywords
        common_themes = self._extract_common_themes(responses)

        for theme, participating in common_themes.items():
            if len(participating) >= 2:
                agreement = Agreement(
                    topic=theme,
                    agreement_level=AgreementLevel.PARTIAL_AGREEMENT,
                    participating_providers=list(participating),
                    consensus_statement=f"Council members agree on aspects of {theme}",
                    supporting_evidence=[f"Mentioned by {p.value}" for p in participating],
                    provenance_breakdown={ClaimProvenance.INFERRED: len(participating)}
                )
                agreements.append(agreement)

        return agreements

    def _identify_conflicts(self, session: CouncilSession) -> List[Conflict]:
        """Identify conflicts between council members"""
        conflicts = []

        # Simple conflict detection - could be enhanced with sentiment analysis
        responses = {}
        for provider, response in session.round1_responses.items():
            if not response.error:
                responses[provider] = response.response_text

        # Look for contradictory keywords
        contradiction_indicators = [
            ("secure", "insecure"),
            ("recommend", "avoid"),
            ("simple", "complex"),
            ("fast", "slow")
        ]

        for pos_term, neg_term in contradiction_indicators:
            pos_providers = []
            neg_providers = []

            for provider, text in responses.items():
                if pos_term.lower() in text.lower():
                    pos_providers.append(provider)
                if neg_term.lower() in text.lower():
                    neg_providers.append(provider)

            if pos_providers and neg_providers:
                positions = {}
                for p in pos_providers:
                    positions[p] = f"Emphasizes {pos_term}"
                for p in neg_providers:
                    positions[p] = f"Emphasizes {neg_term}"

                conflict = Conflict(
                    topic=f"{pos_term} vs {neg_term}",
                    conflict_type="approach",
                    positions=positions,
                    irreconcilable=False,
                    potential_resolution=f"Consider balance between {pos_term} and {neg_term}"
                )
                conflicts.append(conflict)

        return conflicts

    def _extract_common_themes(self, responses: Dict[AIProvider, str]) -> Dict[str, Set[AIProvider]]:
        """Extract common themes across responses"""
        themes = {}

        # Common technical themes
        theme_keywords = {
            "security": ["security", "secure", "authentication", "authorization", "encryption"],
            "performance": ["performance", "speed", "optimization", "latency", "throughput"],
            "scalability": ["scalability", "scale", "growth", "capacity", "distributed"],
            "usability": ["user", "usability", "experience", "interface", "intuitive"],
            "testing": ["test", "testing", "validation", "verification", "quality"]
        }

        for theme, keywords in theme_keywords.items():
            participating = set()
            for provider, text in responses.items():
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in keywords):
                    participating.add(provider)
            if participating:
                themes[theme] = participating

        return themes

    def _extract_insights(self, session: CouncilSession) -> List[str]:
        """Extract key insights from council discussion"""
        insights = []

        # Extract insights from Round 2 cross-review
        for provider, response in session.round2_responses.items():
            if response.error:
                continue

            text = response.response_text

            # Look for insight indicators
            insight_patterns = [
                r'key insight[s]?:?\s*(.+?)(?:\n|$)',
                r'important[ly]?\s*(.+?)(?:\n|$)',
                r'critical[ly]?\s*(.+?)(?:\n|$)',
                r'notably\s*(.+?)(?:\n|$)'
            ]

            for pattern in insight_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    insight = match.group(1).strip()
                    if insight and len(insight) > 10:  # Filter out too short insights
                        insights.append(f"{provider.value}: {insight}")

        return insights

    def _extract_recommendations(self, session: CouncilSession) -> List[str]:
        """Extract action recommendations from council discussion"""
        recommendations = []

        for provider, response in session.round1_responses.items():
            if response.error:
                continue

            text = response.response_text

            # Look for recommendation indicators
            rec_patterns = [
                r'recommend[s]?\s*(.+?)(?:\n|$)',
                r'suggest[s]?\s*(.+?)(?:\n|$)',
                r'should\s*(.+?)(?:\n|$)',
                r'next step[s]?\s*(.+?)(?:\n|$)'
            ]

            for pattern in rec_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    rec = match.group(1).strip()
                    if rec and len(rec) > 15:
                        recommendations.append(f"{provider.value}: {rec}")

        return recommendations

    def _identify_knowledge_gaps(self, session: CouncilSession) -> List[str]:
        """Identify knowledge gaps mentioned by council members"""
        gaps = []

        for provider, response in session.round1_responses.items():
            if response.error:
                continue

            text = response.response_text

            # Look for uncertainty indicators
            gap_patterns = [
                r'unclear\s*(.+?)(?:\n|$)',
                r'unknown\s*(.+?)(?:\n|$)',
                r'need[s]? more information\s*(.+?)(?:\n|$)',
                r'would need to know\s*(.+?)(?:\n|$)',
                r'assumption[s]?\s*(.+?)(?:\n|$)'
            ]

            for pattern in gap_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    gap = match.group(1).strip()
                    if gap and len(gap) > 10:
                        gaps.append(f"{provider.value}: {gap}")

        return gaps

    def _generate_next_questions(self, session: CouncilSession) -> List[str]:
        """Generate next questions based on council analysis"""
        questions = []

        # Extract questions mentioned by council members
        for provider, response in session.round2_responses.items():
            if response.error:
                continue

            text = response.response_text

            # Look for question patterns
            question_patterns = [
                r'question[s]?\s*(.+?\?)',
                r'consider[ing]?\s*(.+?\?)',
                r'what\s+(.+?\?)',
                r'how\s+(.+?\?)',
                r'why\s+(.+?\?)'
            ]

            for pattern in question_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    question = match.group(0).strip()
                    if question and len(question) > 20:
                        questions.append(question)

        return questions

    def _generate_council_summary(
        self,
        session: CouncilSession,
        agreements: List[Agreement],
        conflicts: List[Conflict],
        insights: List[str]
    ) -> str:
        """Generate council summary preserving distinct voices"""

        summary = f"""
=== AI COUNCIL SESSION SUMMARY ===
Session ID: {session.session_id}
User Input: {session.user_input}

=== COUNCIL COMPOSITION ===
"""

        # List participating members
        for provider in session.round1_responses.keys():
            role = {
                AIProvider.CLAUDE: "Architecture & Systems Design",
                AIProvider.GPT4: "Structure & Implementation",
                AIProvider.GEMINI: "User Experience & Interface",
                AIProvider.GROK: "Stress Testing & Edge Cases",
                AIProvider.PERPLEXITY: "Adversarial Analysis & Research"
            }.get(provider, "General Analysis")

            summary += f"• {provider.value.title()}: {role}\n"

        summary += f"""
=== AGREEMENTS IDENTIFIED ===
"""
        if agreements:
            for i, agreement in enumerate(agreements, 1):
                providers = ", ".join([p.value for p in agreement.participating_providers])
                summary += f"{i}. {agreement.topic} ({providers})\n   {agreement.consensus_statement}\n"
        else:
            summary += "No clear agreements identified.\n"

        summary += f"""
=== CONFLICTS IDENTIFIED ===
"""
        if conflicts:
            for i, conflict in enumerate(conflicts, 1):
                summary += f"{i}. {conflict.topic} ({conflict.conflict_type})\n"
                for provider, position in conflict.positions.items():
                    summary += f"   • {provider.value}: {position}\n"
        else:
            summary += "No major conflicts identified.\n"

        summary += f"""
=== KEY INSIGHTS ===
"""
        if insights:
            for insight in insights[:5]:  # Limit to top 5
                summary += f"• {insight}\n"
        else:
            summary += "No explicit insights extracted.\n"

        summary += f"""
=== PRESERVATION OF VOICES ===
All original council member responses are preserved in their entirety.
No merging or blending of perspectives has occurred.
Each voice maintains its distinct analytical approach and conclusions.

=== NEXT STEPS ===
Review individual council member outputs for detailed analysis.
Consider areas of agreement for implementation priorities.
Address conflicts through additional investigation or stakeholder input.
"""

        return summary.strip()

    def export_synthesis(self, synthesis: SynthesisResult) -> Dict[str, Any]:
        """Export synthesis result to JSON-serializable format"""
        return {
            "session_id": synthesis.session_id,
            "synthesis_timestamp": synthesis.synthesis_timestamp.isoformat(),
            "original_outputs": {
                provider.value: {str(round_num): response for round_num, response in rounds.items()}
                for provider, rounds in synthesis.original_outputs.items()
            },
            "agreements": [asdict(agreement) for agreement in synthesis.agreements],
            "conflicts": [asdict(conflict) for conflict in synthesis.conflicts],
            "key_insights": synthesis.key_insights,
            "action_recommendations": synthesis.action_recommendations,
            "knowledge_gaps": synthesis.knowledge_gaps,
            "next_questions": synthesis.next_questions,
            "council_summary": synthesis.council_summary
        }


# Example usage
if __name__ == "__main__":
    # This would typically be called with actual session data
    print("Synthesis Engine initialized - ready for council analysis")