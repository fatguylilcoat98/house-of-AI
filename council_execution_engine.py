"""
Council Execution Engine - Two-Round AI Coordination
Handles Round 1 (independent) and Round 2 (cross-review) execution

Built by Christopher Hughes & The Good Neighbor Guard
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from system_packet_builder import SystemPacketBuilder, SystemPacket


class AIProvider(Enum):
    CLAUDE = "claude"
    GPT4 = "gpt4"
    GEMINI = "gemini"
    GROK = "grok"
    PERPLEXITY = "perplexity"


class ExecutionRound(Enum):
    INDEPENDENT = 1
    CROSS_REVIEW = 2


@dataclass
class AIResponse:
    """Single AI response with metadata"""
    provider: AIProvider
    round_number: int
    response_text: str
    timestamp: datetime
    processing_time_ms: float
    token_count: Optional[int] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class CouncilSession:
    """Complete council session with both rounds"""
    session_id: str
    user_input: str
    system_packet_r1: SystemPacket
    system_packet_r2: Optional[SystemPacket]
    round1_responses: Dict[AIProvider, AIResponse]
    round2_responses: Dict[AIProvider, AIResponse]
    session_start: datetime
    session_end: Optional[datetime]
    total_processing_time_ms: float
    status: str  # "running", "completed", "error"


class CouncilExecutionEngine:
    """Manages two-round execution for AI council"""

    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.packet_builder = SystemPacketBuilder()
        self.sessions: Dict[str, CouncilSession] = {}

        # AI role mapping
        self.ai_roles = {
            AIProvider.CLAUDE: "claude",
            AIProvider.GPT4: "gpt",
            AIProvider.GEMINI: "gemini",
            AIProvider.GROK: "grok",
            AIProvider.PERPLEXITY: "perplexity"
        }

    async def execute_full_council_session(
        self,
        user_input: str,
        session_id: Optional[str] = None
    ) -> CouncilSession:
        """Execute complete two-round council session"""

        if session_id is None:
            session_id = f"council_{int(time.time())}"

        session_start = datetime.now()

        # Round 1: Independent responses
        round1_packet = self.packet_builder.build_packet(user_input, round_number=1)
        round1_responses = await self._execute_round_1(round1_packet)

        # Round 2: Cross-review
        round2_packet = self.packet_builder.build_packet(
            user_input,
            round_number=2,
            previous_outputs=self._format_outputs_for_cross_review(round1_responses)
        )
        round2_responses = await self._execute_round_2(round2_packet)

        session_end = datetime.now()
        total_time = (session_end - session_start).total_seconds() * 1000

        session = CouncilSession(
            session_id=session_id,
            user_input=user_input,
            system_packet_r1=round1_packet,
            system_packet_r2=round2_packet,
            round1_responses=round1_responses,
            round2_responses=round2_responses,
            session_start=session_start,
            session_end=session_end,
            total_processing_time_ms=total_time,
            status="completed"
        )

        self.sessions[session_id] = session
        return session

    async def _execute_round_1(self, packet: SystemPacket) -> Dict[AIProvider, AIResponse]:
        """Execute Round 1: Independent responses"""

        tasks = []
        for provider in AIProvider:
            if provider.value in self.api_keys:
                task = self._call_ai_provider(provider, packet)
                tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        result = {}
        for i, provider in enumerate([p for p in AIProvider if p.value in self.api_keys]):
            if isinstance(responses[i], Exception):
                result[provider] = AIResponse(
                    provider=provider,
                    round_number=1,
                    response_text="",
                    timestamp=datetime.now(),
                    processing_time_ms=0,
                    error=str(responses[i])
                )
            else:
                result[provider] = responses[i]

        return result

    async def _execute_round_2(self, packet: SystemPacket) -> Dict[AIProvider, AIResponse]:
        """Execute Round 2: Cross-review"""
        # Same logic as Round 1, but with cross-review context
        return await self._execute_round_1(packet)

    async def _call_ai_provider(self, provider: AIProvider, packet: SystemPacket) -> AIResponse:
        """Call individual AI provider"""

        start_time = time.time()
        prompt = packet.to_prompt(self.ai_roles[provider])

        try:
            if provider == AIProvider.CLAUDE:
                response_text = await self._call_claude(prompt)
            elif provider == AIProvider.GPT4:
                response_text = await self._call_gpt4(prompt)
            elif provider == AIProvider.GEMINI:
                response_text = await self._call_gemini(prompt)
            elif provider == AIProvider.GROK:
                response_text = await self._call_grok(prompt)
            elif provider == AIProvider.PERPLEXITY:
                response_text = await self._call_perplexity(prompt)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            processing_time = (time.time() - start_time) * 1000

            return AIResponse(
                provider=provider,
                round_number=packet.round_number,
                response_text=response_text,
                timestamp=datetime.now(),
                processing_time_ms=processing_time
            )

        except Exception as e:
            return AIResponse(
                provider=provider,
                round_number=packet.round_number,
                response_text="",
                timestamp=datetime.now(),
                processing_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_keys["claude"],
                    "content-type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def _call_gpt4(self, prompt: str) -> str:
        """Call GPT-4 API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_keys['gpt4']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_keys['gemini']}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 4000}
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_grok(self, prompt: str) -> str:
        """Call Grok API - placeholder implementation"""
        # Note: Actual Grok API endpoint and format may differ
        # This is a placeholder for the expected integration
        return f"[GROK PLACEHOLDER] Stress testing analysis of: {prompt[:100]}..."

    async def _call_perplexity(self, prompt: str) -> str:
        """Call Perplexity API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_keys['perplexity']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _format_outputs_for_cross_review(
        self,
        round1_responses: Dict[AIProvider, AIResponse]
    ) -> Dict[str, Any]:
        """Format Round 1 outputs for Round 2 cross-review"""

        formatted = {}
        for provider, response in round1_responses.items():
            if response.error:
                formatted[provider.value] = {
                    "status": "error",
                    "error": response.error
                }
            else:
                formatted[provider.value] = {
                    "status": "success",
                    "response": response.response_text,
                    "timestamp": response.timestamp.isoformat(),
                    "processing_time_ms": response.processing_time_ms
                }

        return formatted

    def get_session(self, session_id: str) -> Optional[CouncilSession]:
        """Retrieve session by ID"""
        return self.sessions.get(session_id)

    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session data"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session_id,
            "user_input": session.user_input,
            "round1_responses": {
                provider.value: {
                    "response": resp.response_text,
                    "timestamp": resp.timestamp.isoformat(),
                    "processing_time_ms": resp.processing_time_ms,
                    "error": resp.error
                }
                for provider, resp in session.round1_responses.items()
            },
            "round2_responses": {
                provider.value: {
                    "response": resp.response_text,
                    "timestamp": resp.timestamp.isoformat(),
                    "processing_time_ms": resp.processing_time_ms,
                    "error": resp.error
                }
                for provider, resp in session.round2_responses.items()
            },
            "session_start": session.session_start.isoformat(),
            "session_end": session.session_end.isoformat() if session.session_end else None,
            "total_processing_time_ms": session.total_processing_time_ms,
            "status": session.status
        }


# Example usage
if __name__ == "__main__":
    async def test_council():
        api_keys = {
            "claude": "test_key",
            "gpt4": "test_key",
            "gemini": "test_key",
            "perplexity": "test_key"
        }

        engine = CouncilExecutionEngine(api_keys)

        # Test session execution
        session = await engine.execute_full_council_session(
            "Help me design a secure authentication system for a web application"
        )

        print(f"Session completed: {session.session_id}")
        print(f"Total time: {session.total_processing_time_ms:.2f}ms")
        print(f"Round 1 responses: {len(session.round1_responses)}")
        print(f"Round 2 responses: {len(session.round2_responses)}")

    # asyncio.run(test_council())