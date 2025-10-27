# core/fetchers/base_fetcher.py

from abc import ABC, abstractmethod
from core.models.chain_models import ChainFeed

class ChainFetcher(ABC):
    """Provider-agnostic contract for fetching option chain data."""

    @abstractmethod
    def fetch(self, symbol: str) -> ChainFeed:
        """Fetch raw chain data and return a canonical ChainFeed object."""
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider (e.g. 'Polygon', 'Tradier')."""
        pass