"""FX rates data source placeholder implementations."""

from __future__ import annotations

from typing import Iterable

from app.data_sources.base import DataSource
from app.models import MarketDatum


class FXRatesSource(DataSource):
    """Collect currency quotes and spreads for the digest."""

    name = "fx_rates"
    category = "currencies"

    async def pull(self) -> Iterable[MarketDatum]:
        raise NotImplementedError("FXRatesSource.pull is not implemented yet")
