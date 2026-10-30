import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from .schemas import AgentRequest, AnalyzeRequest
from .agent import run_agent, direct_analysis

app = FastAPI(title="CodePilot AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.get("/")
def root():
    return {"name": "CodePilot AI", "status": "online", "track": "Coding and Agentic Engineering"}

@app.get("/api/health")
def health():
    return {"status": "ok", "provider": "Nebius Token Factory", "model_configured": bool(os.getenv("NEBIUS_API_KEY"))}

@app.post("/api/analyze")
def analyze(payload: AnalyzeRequest):
    try:
        return {"result": direct_analysis(payload.task_type, payload.code, payload.language)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@app.post("/api/agent/run")
def agent_run(payload: AgentRequest):
    try:
        return run_agent(payload.task, payload.task_type, [f.model_dump() for f in payload.files])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
