"""OpenAI GPT implementation of the digest generation service."""

from __future__ import annotations

from typing import Sequence

from app.models import DigestPayload, MarketDatum


class GptDigestService:
    """Generate digests using OpenAI's GPT models."""

    def __init__(self, api_key: str, model: str = "gpt-4.1-mini") -> None:
        self._api_key = api_key
        self._model = model

    async def build_digest(self, snapshots: Sequence[MarketDatum]) -> DigestPayload:
        """Call OpenAI API with structured prompt and assemble a digest."""

        raise NotImplementedError("GptDigestService.build_digest is not implemented yet")
