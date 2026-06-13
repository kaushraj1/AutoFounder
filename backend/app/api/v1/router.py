"""Aggregate router for API v1."""

from fastapi import APIRouter

from app.api.v1 import (
    artifacts,
    devops_approvals,
    feedback,
    gates,
    ideas,
    llmops,
    runs,
)

api_router = APIRouter()
api_router.include_router(ideas.router)
api_router.include_router(runs.router)
api_router.include_router(gates.router)
api_router.include_router(devops_approvals.router)
api_router.include_router(artifacts.router)
api_router.include_router(feedback.router)
api_router.include_router(llmops.router)
