"""HTTP routes for manual refresh and digest history."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import DependencyProvider
from app.models import DigestPayload
from app.orchestrator import DigestOrchestrator
from app.repositories.digests import DigestRepository


def create_router(provider: DependencyProvider) -> APIRouter:
    """Create an API router bound to the provided dependencies."""

    router = APIRouter()

    @router.post("/admin/refresh", response_model=DigestPayload)
    async def manual_refresh(
        orchestrator: DigestOrchestrator = Depends(provider.orchestrator),
    ) -> DigestPayload:
        return await orchestrator.run_cycle()

    @router.get("/digests", response_model=list[DigestPayload])
    async def list_digests(
        repository: DigestRepository = Depends(provider.repository),
        limit: int = 30,
    ) -> list[DigestPayload]:
        history = await repository.history(limit=limit)
        return list(history)

    return router
