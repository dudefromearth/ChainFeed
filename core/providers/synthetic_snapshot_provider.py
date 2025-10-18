# core/providers/synthetic_snapshot_provider.py

import datetime
from typing import Optional, List, Dict
from core.providers.chain_snapshot_provider import ChainSnapshotProvider


class SyntheticSnapshotProvider(ChainSnapshotProvider):
    def __init__(
        self,
        symbol: str,
        expiration: Optional[str] = None,
        contracts: Optional[List[Dict]] = None
    ):
        super().__init__(symbol, expiration)
        self.contracts = contracts or self._generate_mock_contracts()

    def fetch_chain_snapshot(self) -> dict:
        """Return a synthetic (simulated) snapshot of an options chain."""
        return {
            "symbol": self.symbol,
            "expiration": self.expiration or self._default_expiration(),
            "generated": True,
            "contracts": self.contracts
        }

    def _default_expiration(self) -> str:
        """Return a default expiration date (7 days from today)."""
        return (datetime.date.today() + datetime.timedelta(days=7)).isoformat()

    def _generate_mock_contracts(self) -> List[Dict]:
        """Generate mock call and put contracts."""
        expiration = self.expiration or self._default_expiration()
        return [
            {
                "ticker": f"O:{self.symbol}240101C00400000",
                "strike": 400,
                "contract_type": "call",
                "expiration_date": expiration,
                "bid": 12.5,
                "ask": 13.0
            },
            {
                "ticker": f"O:{self.symbol}240101P00400000",
                "strike": 400,
                "contract_type": "put",
                "expiration_date": expiration,
                "bid": 10.2,
                "ask": 10.7
            }
        ]