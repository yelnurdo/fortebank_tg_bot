"""Basic daily scheduler for digest auto-dispatch."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta, timezone

from app.orchestrator import DigestOrchestrator

logger = logging.getLogger(__name__)


class Scheduler:
    """Runs the orchestrator every day at the configured dispatch time."""

    def __init__(self, orchestrator: DigestOrchestrator, dispatch_time: time) -> None:
        self._orchestrator = orchestrator
        self._dispatch_time = dispatch_time
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._worker())

    async def _worker(self) -> None:
        while True:
            now = datetime.now(tz=timezone.utc)
            target = now.replace(
                hour=self._dispatch_time.hour,
                minute=self._dispatch_time.minute,
                second=0,
                microsecond=0,
            )
            if target <= now:
                target = target + timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            logger.info("Scheduler sleeping for %.2f seconds", wait_seconds)
            await asyncio.sleep(wait_seconds)
            try:
                await self._orchestrator.run_cycle()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Digest cycle failed: %s", exc)
