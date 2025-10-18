from abc import ABC, abstractmethod
from typing import Optional, Union
from datetime import date


class ChainSnapshotProvider(ABC):
    """
    Abstract base class for all chain snapshot providers.
    """

    def __init__(self, symbol: str, expiration: Optional[str] = None):
        self.symbol = symbol
        self.expiration = expiration

    def fetch(self) -> Optional[dict]:
        """
        Generic fetch entrypoint. Subclasses can override this or just implement `fetch_chain_snapshot()`.
        """
        return self.fetch_chain_snapshot()

    @abstractmethod
    def fetch_chain_snapshot(self) -> Optional[dict]:
        """
        Subclasses must implement this to fetch the actual snapshot data.
        Should return a normalized dictionary.
        """
        pass