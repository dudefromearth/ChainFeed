"""
core/providers/historical_provider.py
──────────────────────────────────────────────
Retrieves historical options chain snapshots.

Two operational modes:
- API mode: Fetch from Polygon.io if POLYGON_API_KEY is set
- Offline mode: Load from a local JSON file (for testing / historical replay)
──────────────────────────────────────────────
"""

import os
import json
import warnings
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any
import requests

from core.providers.chain_snapshot_provider import ChainSnapshotProvider
from core.chain_normalizer import normalize_snapshot  # must exist or be stubbed


POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
BASE_CONTRACT_URL = "https://api.polygon.io/v3/reference/options/contracts"


class HistoricalSnapshotProvider(ChainSnapshotProvider):
    """
    Retrieves a historical options chain snapshot for a given symbol,
    expiration date, and snapshot_date (as_of date).
    """

    def __init__(
        self,
        symbol: str,
        expiration: Optional[str] = None,
        snapshot_date: Optional[str] = None
    ):
        super().__init__(symbol, expiration)
        self.snapshot_date = snapshot_date or date.today().isoformat()

    # ──────────────────────────────────────────────
    # Primary fetch logic (Polygon API)
    # ──────────────────────────────────────────────
    def fetch_chain_snapshot(self) -> Optional[Dict[str, Any]]:
        """Fetch from Polygon API (if POLYGON_API_KEY is set)."""
        if not POLYGON_API_KEY:
            warnings.warn("⚠️ POLYGON_API_KEY not set. Falling back to local file sample.")
            return None

        if not self.expiration:
            warnings.warn(
                f"HistoricalSnapshotProvider for {self.symbol} requires an expiration date.",
                category=UserWarning
            )
            return None

        params = {
            "underlying_ticker": self.symbol,
            "apiKey": POLYGON_API_KEY,
            "as_of": self.snapshot_date,
            "expiration_date": self.expiration,
        }

        try:
            res = requests.get(BASE_CONTRACT_URL, params=params)
            res.raise_for_status()
            body = res.json()
            contracts = body.get("results", [])
            if not contracts:
                warnings.warn(
                    f"No historical contracts found for {self.symbol} as of {self.snapshot_date} "
                    f"with expiration {self.expiration}.",
                    category=UserWarning
                )
                return None

            normalized = normalize_snapshot(contracts)
            normalized["symbol"] = self.symbol
            normalized["expiration"] = self.expiration
            normalized["snapshot_date"] = self.snapshot_date
            normalized["fetched_at"] = datetime.now(timezone.utc).isoformat()
            return normalized

        except Exception as e:
            warnings.warn(
                f"Failed to fetch historical snapshot for {self.symbol} on {self.snapshot_date}: {e}",
                category=RuntimeWarning
            )
            return None

    # ──────────────────────────────────────────────
    # Local file loader (used by historical_feed_manager)
    # ──────────────────────────────────────────────
    def load_snapshot(self, path: str) -> Dict[str, Any]:
        """
        Load a historical snapshot from a local JSON file.
        Automatically adds symbol, snapshot_date, and UTC timestamp.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ Snapshot file not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        # Add metadata
        data["symbol"] = data.get("symbol", self.symbol)
        data["snapshot_date"] = data.get("snapshot_date", self.snapshot_date)
        data["loaded_at"] = datetime.now(timezone.utc).isoformat()

        return data