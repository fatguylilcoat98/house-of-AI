# AI Council System - Clean Architecture Design

## System Requirements

### 1. System Packet Builder
- **Constitution Core**: User's core values/rules
- **Active System State**: Current project/context state  
- **Session Goal**: What we're trying to achieve
- **User Input**: The actual message/request

### 2. Two-Round Execution
- **Round 1**: Independent responses from all 5 AI
- **Round 2**: Cross-review using actual outputs from Round 1

### 3. Synthesis Engine (Modified)
- **DO NOT merge voices** - preserve distinct perspectives
- **Show agreements + conflicts** clearly
- **Preserve original outputs** intact

### 4. Claim Tagging (Provenance)
- **Measured**: Based on data/evidence
- **Inferred**: Logical deduction
- **Assumed**: Assumptions made
- **Generated**: Created/hypothetical

### 5. Save/Capture System
- Name and store key outputs for later reference
- Build knowledge base over time

### 6. Active System State Panel
- Editable state that persists across sessions
- User can update context/goals

### 7. Exportable Handoff Packet
- Package complete session for external use
- Include all outputs, decisions, state

### 8. Sole Carrier Rule
- No assumption of cross-AI memory
- Each interaction is complete and self-contained

### 9. Correction Mechanism
- Allow updating incorrect outputs after delivery
- Version tracking for corrections

### 10. Role Alignment
- **Claude**: Architecture & Systems Design
- **GPT-4**: Structure & Implementation  
- **Gemini**: User Experience & Interface
- **Grok**: Stress Testing & Edge Cases
- **Perplexity**: Adversarial Analysis & Research

## Technical Stack
- **Backend**: FastAPI (keep existing foundation)
- **Frontend**: Clean, functional interface (strip NymbleLogic UI)
- **APIs**: Claude, GPT-4, Gemini, Grok, Perplexity
- **Storage**: Local state + export capabilities
- **Architecture**: Microservices for each component

## Data Flow
```
User Input → System Packet Builder → Round 1 (Parallel) → Round 2 (Cross-Review) → Synthesis → Save/Export
```

## Security & Privacy
- Sole Carrier rule ensures no cross-AI data leakage
- All state explicitly managed
- Export controls for sensitive data