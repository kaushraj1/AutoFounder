"""Aggregate router for API v1."""

from fastapi import APIRouter

from app.api.v1 import ideas, runs

api_router = APIRouter()
api_router.include_router(ideas.router)
api_router.include_router(runs.router)
