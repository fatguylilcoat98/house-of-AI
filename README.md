# House of AI — Veracore Coordination Layer
**The Good Neighbor Guard**

A dead-simple backend that sends your Veracore task to Claude, GPT, and Gemini simultaneously, then shows all three responses side by side with a consensus summary.

---

## Deploy to Render

1. Push this repo to GitHub (`fatguylilcoat98/house-of-ai` or similar)
2. On Render → New → Web Service → connect your repo
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add these **Environment Variables** in Render dashboard:

| Key | Value |
|-----|-------|
| `ANTHROPIC_API_KEY` | your Claude key |
| `OPENAI_API_KEY` | your GPT key |
| `GEMINI_API_KEY` | your Gemini key |

6. Deploy. Visit your Render URL. Done.

---

## How it works

- You type a task (and optional context from a prior phase)
- All three AIs respond in parallel — no waiting for one before the next
- A consensus engine (Claude doing a meta-read) flags agreements and conflicts
- You make the call — you're still the architect

## Repo structure

```
house-of-ai/
├── main.py           # FastAPI backend
├── requirements.txt
├── render_start.sh
└── static/
    └── index.html    # Frontend UI
```

## Keyboard shortcut
`Ctrl + Enter` in the task box to submit.
