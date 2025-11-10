"""Google Gemini implementation of the digest generation service."""

from __future__ import annotations

from typing import Sequence

from app.models import DigestPayload, MarketDatum


class GeminiDigestService:
    """Generate digests using Google Gemini models."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro") -> None:
        self._api_key = api_key
        self._model = model

    async def build_digest(self, snapshots: Sequence[MarketDatum]) -> DigestPayload:
        """Call Gemini API with structured prompt and assemble a digest."""

        raise NotImplementedError("GeminiDigestService.build_digest is not implemented yet")