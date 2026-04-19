# AI Council System - Clean Architecture

**The Good Neighbor Guard - Unified AI Council**

A sophisticated multi-AI coordination system with System Packet Builder, 2-round execution, claim tagging, and comprehensive synthesis capabilities.

---

## 🏛️ Council Architecture

### Council Members & Roles

| AI | Role | Focus Area |
|---|---|---|
| **Claude** | Architecture & Systems Design | Structural decisions, technical approaches, system-level considerations |
| **GPT-4** | Structure & Implementation | Implementation details, code organization, development approaches |
| **Gemini** | User Experience & Interface | Usability, design decisions, user interaction patterns |
| **Grok** | Stress Testing & Edge Cases | Potential failures, edge cases, system limits |
| **Perplexity** | Adversarial Analysis & Research | Challenge assumptions, counterarguments, alternatives |

### Key Features

✅ **System Packet Builder** - Comprehensive context injection  
✅ **Two-Round Execution** - Independent analysis + cross-review  
✅ **Claim Tagging** - Provenance tracking (measured/inferred/assumed/generated)  
✅ **Synthesis Engine** - Preserves distinct voices, identifies agreements/conflicts  
✅ **Save/Capture System** - Named output storage and retrieval  
✅ **Active System State** - Editable persistent context  
✅ **Handoff Packets** - Exportable session packages  
✅ **Sole Carrier Rule** - No cross-AI memory assumptions  
✅ **Correction Mechanism** - Post-delivery output updates  

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone <your-repo>
cd house-of-AI-council-clean
pip install -r requirements.txt
```

### 2. Environment Setup

Create `.env` file:

```env
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_gpt4_key
GEMINI_API_KEY=your_gemini_key
GROK_API_KEY=your_grok_key
PERPLEXITY_API_KEY=your_perplexity_key
```

### 3. Start Council System

```bash
python main_council.py
```

Visit: `http://localhost:8000/static/council_interface.html`
