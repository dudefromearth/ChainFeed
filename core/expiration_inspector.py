"""
core/expiration_inspector.py
----------------------------

ExpirationInspector (Mesh-Aware)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Responsible for retrieving and managing valid option expiration dates
for a given underlying symbol using the Polygon.io API.

Now mesh-aware:
    • Publishes valid expirations into Redis (for shared node access)
    • Uses canonical Redis keys from chainfeed_constants.py
    • Provides metadata for FrontEnd Admin UI (last_updated, count)
    • Includes structured logging for observability

Primary Redis Keys:
    - chainfeed:{symbol}:expirations   → JSON list of expirations
    - chainfeed:meta:expirations       → summary metadata for all symbols

Typical Usage:
    insp = ExpirationInspector("SPX", max_dte=10)
    insp.fetch_expirations()
    insp.publish_to_redis()
"""

import os
import datetime
import json
import requests
from typing import List, Optional
from datetime import timezone
from utils.logger import get_logger
from utils.redis_client import get_redis_client
from config.chainfeed_constants import (
    REDIS_KEYS,
    REDIS_PREFIX,
    HEARTBEAT_VERSION,
)

# ----------------------------------------------------------
# Environment and API Endpoints
# ----------------------------------------------------------
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
BASE_EXPIRATION_URL = "https://api.polygon.io/v3/reference/options/expirations"
BASE_CONTRACT_URL = "https://api.polygon.io/v3/reference/options/contracts"

# ----------------------------------------------------------
# Logging and Redis setup
# ----------------------------------------------------------
logger = get_logger("expiration.inspector")
redis = get_redis_client()


# ----------------------------------------------------------
# Expiration Inspector
# ----------------------------------------------------------
class ExpirationInspector:
    """
    Retrieve, manage, and publish valid expiration dates for a symbol.

    Attributes:
        symbol (str): The underlying ticker (e.g., SPX, NDX).
        max_dte (int): Maximum days to expiration window (default 10).
        expirations (List[str]): Cached expiration dates (ISO strings).
        last_updated (Optional[datetime.datetime]): UTC timestamp of last update.
    """

    def __init__(self, symbol: str, max_dte: int = 10):
        self.symbol = symbol.upper()
        self.max_dte = max_dte
        self.expirations: List[str] = []
        self.last_updated: Optional[datetime.datetime] = None

    # ------------------------------------------------------
    # Utility Functions
    # ------------------------------------------------------
    def get_today_str(self) -> str:
        """Return today's date as an ISO string (YYYY-MM-DD)."""
        return datetime.date.today().isoformat()

    # ------------------------------------------------------
    # Expiration Fetch Logic
    # ------------------------------------------------------
    def fetch_expirations(self) -> None:
        """
        Fetch valid expiration dates for the underlying symbol.

        Tries the primary Polygon expirations endpoint first.
        If unavailable, falls back to the contracts endpoint to derive expirations.
        """
        today = self.get_today_str()
        url = f"{BASE_EXPIRATION_URL}?underlying_ticker={self.symbol}&apiKey={POLYGON_API_KEY}&as_of={today}"

        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
            self.expirations = sorted(data.get("results", []))
            if self.expirations:
                self.last_updated = datetime.datetime.now(timezone.utc)
                logger.info(
                    f"✅ Expirations fetched for {self.symbol} | count={len(self.expirations)}"
                )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"⚠️ Expiration endpoint failed for {self.symbol}, falling back to contracts..."
                )
                self.expirations = self._derive_expirations_from_contracts(today)
                if self.expirations:
                    self.last_updated = datetime.datetime.now(timezone.utc)
            else:
                logger.error(
                    f"❌ HTTP error while fetching expirations for {self.symbol}: {e}",
                    exc_info=True,
                )
        except Exception as e:
            logger.error(
                f"❌ Unexpected error fetching expirations for {self.symbol}: {e}",
                exc_info=True,
            )

    def _derive_expirations_from_contracts(self, as_of: str) -> List[str]:
        """
        Fallback method: fetch options contracts and derive unique expirations.

        Args:
            as_of (str): Date context for contract lookup (ISO string).

        Returns:
            List[str]: Sorted list of expiration dates.
        """
        url = f"{BASE_CONTRACT_URL}?underlying_ticker={self.symbol}&apiKey={POLYGON_API_KEY}&as_of={as_of}"
        expirations = set()
        try:
            res = requests.get(url)
            res.raise_for_status()
            contracts = res.json().get("results", [])
            logger.info(f"✅ {self.symbol} fallback contracts retrieved: {len(contracts)}")

            for contract in contracts:
                exp = contract.get("expiration_date")
                if exp:
                    expirations.add(exp)

        except Exception as e:
            logger.error(f"❌ Failed to derive expirations from contracts: {e}", exc_info=True)
        return sorted(expirations)

    # ------------------------------------------------------
    # Redis Publication
    # ------------------------------------------------------
    def publish_to_redis(self) -> None:
        """
        Publish current expiration list and metadata to Redis
        under canonical ChainFeed key structure.

        Keys:
            chainfeed:{symbol}:expirations  -> JSON list of expirations
            chainfeed:meta:expirations      -> per-symbol summary metadata
        """
        if not self.expirations:
            logger.warning(f"⚠️ No expirations to publish for {self.symbol}.")
            return

        try:
            exp_key = REDIS_KEYS["feed_expirations"].format(symbol=self.symbol)
            meta_key = f"{REDIS_PREFIX}:meta:expirations"

            payload = json.dumps(self.expirations)
            redis.set(exp_key, payload)

            summary = {
                "symbol": self.symbol,
                "count": len(self.expirations),
                "last_updated": (
                    self.last_updated.isoformat() if self.last_updated else None
                ),
                "version": HEARTBEAT_VERSION,
            }

            redis.hset(meta_key, self.symbol, json.dumps(summary))
            logger.info(
                f"📡 Published expirations for {self.symbol} to Redis | count={len(self.expirations)}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to publish expirations for {self.symbol}: {e}", exc_info=True)

    # ------------------------------------------------------
    # Validation / Helpers
    # ------------------------------------------------------
    def is_valid_expiration(self, date_str: str) -> bool:
        """Return True if given ISO date is a valid expiration."""
        return date_str in self.expirations

    def list_valid_expirations(self, limit_dte: Optional[int] = None) -> List[str]:
        """Return list of expirations within max DTE window (default self.max_dte)."""
        limit = limit_dte or self.max_dte
        today = datetime.date.today()
        return [
            exp
            for exp in self.expirations
            if 0 <= (datetime.date.fromisoformat(exp) - today).days <= limit
        ]

    def summary(self) -> dict:
        """Return metadata summary for this symbol."""
        return {
            "symbol": self.symbol,
            "valid_expirations": self.list_valid_expirations(),
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
        }