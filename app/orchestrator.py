"""Digest pipeline orchestrator coordinating data collection and delivery."""

from __future__ import annotations

import logging
from typing import Iterable, Sequence

from app.data_sources.base import DataSource
from app.models import DigestPayload, MarketDatum
from app.repositories.digests import DigestRepository
from app.services.llm import LlmDigestService
from app.telegram.notifier import TelegramNotifier

logger = logging.getLogger(__name__)


class DigestOrchestrator:
    """High-level workflow: collect data → summarize → persist → notify."""

    def __init__(
        self,
        data_sources: Sequence[DataSource],
        generator: LlmDigestService,
        repository: DigestRepository,
        notifier: TelegramNotifier,
    ) -> None:
        self._sources = data_sources
        self._generator = generator
        self._repository = repository
        self._notifier = notifier

    async def run_cycle(self) -> DigestPayload:
        logger.info("Starting data collection cycle")
        snapshots: list[MarketDatum] = []
        for source in self._sources:
            pulled: Iterable[MarketDatum] = await source.pull()
            snapshots.extend(pulled)
        logger.info("Collected %d market records", len(snapshots))

        digest = await self._generator.build_digest(tuple(snapshots))
        await self._repository.save(digest)
        await self._notifier.send_digest(digest)
        logger.info("Digest dispatched successfully")
        return digest
