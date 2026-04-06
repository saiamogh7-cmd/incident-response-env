"""
FastAPI application for the DevOps Incident Response OpenEnv simulation.
"""

from contextlib import asynccontextmanager
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from server.environment import IncidentResponseEnv
    from server.models import IncidentAction, IncidentObservation, StepResult, EpisodeState
except ImportError:
    from environment import IncidentResponseEnv
    from models import IncidentAction, IncidentObservation, StepResult, EpisodeState

# Global environment instance
env: Optional[IncidentResponseEnv] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global env
    env = IncidentResponseEnv(task_level="easy")
    env.reset()
    yield
    if env:
        env.close()

app = FastAPI(title="Incident Response Env API", lifespan=lifespan)

# CORS required for HF Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    if "Episode is done" in str(exc):
        return JSONResponse(status_code=400, content={"error": "Episode done, call /reset first"})
    return JSONResponse(status_code=400, content={"error": str(exc)})


class ResetRequest(BaseModel):
    task_level: str
    scenario_id: Optional[str] = None


@app.post("/reset", response_model=IncidentObservation)
async def reset_env(req: ResetRequest):
    global env
    env = IncidentResponseEnv(task_level=req.task_level)
    obs = env.reset(scenario_id=req.scenario_id)
    return obs


@app.post("/step", response_model=StepResult)
async def step_env(action: IncidentAction):
    global env
    if not env:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    if env.done:
        raise HTTPException(status_code=400, detail="Episode done, call /reset first")
        
    return env.step(action)


@app.get("/state", response_model=EpisodeState)
async def get_state():
    global env
    if not env:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    return env.state()


@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": "incident-response-env", "version": "1.0.0"}


@app.get("/tasks")
async def list_tasks():
    return [
        {"name": "easy", "description": "Identify the failing service from logs and metrics", "max_steps": 8},
        {"name": "medium", "description": "Write a remediation runbook for a cascading failure", "max_steps": 8},
        {"name": "hard", "description": "Diagnose multi-service cascading failure and write a postmortem", "max_steps": 8}
    ]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860)
