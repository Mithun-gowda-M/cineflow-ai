"""AI Director storyboarding, prompt planning, and Ollama status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.ai_director.director import DirectorNoFootageError, generate_director_plan
from backend.ai_director.ollama_client import check_ollama_status
from backend.api.config import get_settings
from backend.api.schemas import (
    DirectorPlanRequest,
    DirectorPlanResponse,
    DirectorStatusResponse,
)

router = APIRouter(prefix="/director", tags=["AI Director"])


@router.get("/status", response_model=DirectorStatusResponse)
async def get_director_status() -> DirectorStatusResponse:
    """Report whether local Ollama is reachable alongside guaranteed fallback status."""
    settings = get_settings()
    available, models = await check_ollama_status()
    return DirectorStatusResponse(
        ollama_available=available,
        ollama_url=settings.OLLAMA_BASE_URL,
        configured_model=settings.OLLAMA_MODEL,
        available_models=models,
        fallback_ready=True,
    )


@router.post("/plan", response_model=DirectorPlanResponse)
async def create_director_plan(request: DirectorPlanRequest) -> DirectorPlanResponse:
    """Generate a validated 4-act storyboard and `TimelinePlan` from natural instructions."""
    try:
        return await generate_director_plan(request)
    except DirectorNoFootageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

