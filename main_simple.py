"""
Minimal FastAPI app for testing Render deployment
"""

from fastapi import FastAPI

app = FastAPI(title="AI Council Test")

@app.get("/")
async def root():
    return {"message": "AI Council System - Test Deployment", "status": "ok"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "message": "Minimal deployment working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000)