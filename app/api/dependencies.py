"""FastAPI dependency wiring helpers."""

from __future__ import annotations

from app.orchestrator import DigestOrchestrator
from app.repositories.digests import DigestRepository


class DependencyProvider:
    """Simple container for lazy dependency access."""

    def __init__(self, orchestrator: DigestOrchestrator, repository: DigestRepository) -> None:
        self._orchestrator = orchestrator
        self._repository = repository

    def orchestrator(self) -> DigestOrchestrator:
        return self._orchestrator

    def repository(self) -> DigestRepository:
        return self._repository
