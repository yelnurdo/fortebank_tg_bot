"""Persistence layer for digests in PostgreSQL."""

from __future__ import annotations

from typing import Sequence

from app.models import DigestPayload


class DigestRepository:
    """Store and retrieve generated digests."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def save(self, digest: DigestPayload) -> None:
        raise NotImplementedError("DigestRepository.save is not implemented yet")

    async def history(self, limit: int = 30) -> Sequence[DigestPayload]:
        raise NotImplementedError("DigestRepository.history is not implemented yet")
