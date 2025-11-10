"""Shared domain models for digests and market data."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class MarketDatum(BaseModel):
	"""Normalized raw snapshot from any monitored source."""

	source: str
	category: str
	payload: dict[str, Any]
	retrieved_at: datetime


class DigestSection(BaseModel):
	"""Group of insights for a particular market category."""

	title: str
	bullet_points: list[str]


class DigestPayload(BaseModel):
	"""LLM-generated digest ready for delivery."""

	generated_at: datetime
	quote_date: datetime
	sections: list[DigestSection]
	recommendation: str | None = None
