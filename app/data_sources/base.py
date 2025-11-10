"""Abstract base classes for market data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from app.models import MarketDatum


class DataSource(ABC):
    """Contract for any external market data source."""

    name: str
    category: str

    @abstractmethod
    async def pull(self) -> Iterable[MarketDatum]:
        """Fetch the latest data snapshot from the upstream source."""

