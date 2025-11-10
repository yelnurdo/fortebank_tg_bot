"""Telegram delivery adapter for digest notifications."""

from __future__ import annotations

from app.models import DigestPayload


class TelegramNotifier:
    """Send digest summaries to Telegram recipients."""

    def __init__(self, bot_token: str) -> None:
        self._bot_token = bot_token

    async def send_digest(self, digest: DigestPayload) -> None:
        raise NotImplementedError("TelegramNotifier.send_digest is not implemented yet")
