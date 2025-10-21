import datetime
import warnings
from typing import Optional, Dict
from core.providers.chain_snapshot_provider import ChainSnapshotProvider
from core.fetch_chain_snapshot import fetch_chain_snapshot
from core.expiration_inspector import ExpirationInspector


class LiveSnapshotProvider(ChainSnapshotProvider):
    """
    Provides live (real-time) options chain snapshots.
    If no expiration is supplied, attempts to use today's expiration,
    but warns gracefully if today is not a valid trading or expiration day.
    """

    def __init__(self, symbol: str, expiration: Optional[str] = None):
        super().__init__(symbol, expiration)

    def fetch_chain_snapshot(self) -> Optional[Dict]:
        """
        Fetch a real-time options chain snapshot.

        - If today is a valid expiration, fetch and return the chain.
        - If today is not valid and no expiration provided, warn gracefully and return None.
        - Always warns (not prints) for non-critical issues so tests and logs can capture them.
        """
        inspector = ExpirationInspector(self.symbol)
        inspector.fetch_expirations()

        # Resolve expiration: use provided, or check if today is valid
        if not self.expiration:
            today = inspector.get_today_str()
            if not inspector.is_valid_expiration(today):
                next_valid = inspector.get_next_valid_expiration()
                warnings.warn(
                    f"{today} is not a valid expiration for {self.symbol}. "
                    f"Next valid expiration is {next_valid}.",
                    category=UserWarning
                )
                return None
            self.expiration = today

        # Double-check provided expiration validity
        if not inspector.is_valid_expiration(self.expiration):
            warnings.warn(
                f"Expiration {self.expiration} is not valid for {self.symbol}.",
                category=UserWarning
            )
            return None

        # Compute days to expiration (DTE)
        today = datetime.date.today()
        exp_date = datetime.date.fromisoformat(self.expiration)
        dte = (exp_date - today).days

        try:
            snapshot = fetch_chain_snapshot(self.symbol, dte=dte)
            if not isinstance(snapshot, dict):
                warnings.warn(
                    f"Unexpected snapshot type for {self.symbol}: {type(snapshot)}",
                    category=RuntimeWarning
                )
                return None
            return snapshot

        except Exception as e:
            warnings.warn(
                f"Failed to fetch live snapshot for {self.symbol}: {e}",
                category=RuntimeWarning
            )
            return None