from abc import ABC, abstractmethod
from core.models.chain_models import ChainFeed

class ChainFetcher(ABC):
    """
    Abstract interface for retrieving and transforming provider data into canonical ChainFeed objects.
    The fetcher itself does not know or care about the feed type (raw/full/diff).
    """

    @property
    @abstractmethod
    def provider(self) -> str:
        """Return provider name (e.g., 'Polygon.io')."""
        pass

    @abstractmethod
    def get_raw_data(self, endpoint: str, params: dict) -> dict:
        """
        Retrieve data from the provider using the given endpoint and params.
        This is the only point where REST or WebSocket transport is aware.
        """
        pass

    @abstractmethod
    def fetch(self, symbol: str, mode: str = "raw") -> ChainFeed:
        """
        Fetch data for the given symbol and mode ('raw', 'full', 'diff').
        The mode determines the endpoint used, not behavior.
        """
        pass