"""Investment products data source placeholder implementations."""

from __future__ import annotations

from typing import Iterable

from app.data_sources.base import DataSource
from app.models import MarketDatum


class InvestmentsSource(DataSource):
    """Collect investment offers and yields for the digest."""

    name = "investments"
    category = "investments"

    async def pull(self) -> Iterable[MarketDatum]:
        raise NotImplementedError("InvestmentsSource.pull is not implemented yet")
