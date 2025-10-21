"""
core/feed_bootstrap.py
----------------------

Feed Bootstrap Coordinator

Ensures that all required metadata (e.g., expirations) is validated and cached
before any feed manager is instantiated. Acts as a guard layer between
system startup and feed activation.

Responsibilities:
  - Check Redis for cached expirations for the target symbol
  - Fetch and publish expirations via ExpirationInspector if missing
  - Return readiness status (True/False)
"""

import json
from utils.logger import get_logger
from utils.redis_client import get_redis_client
from core.expiration_inspector import ExpirationInspector
from config.chainfeed_constants import REDIS_KEYS

logger = get_logger("feed.bootstrap")
redis = get_redis_client()


class FeedBootstrap:
    """
    Ensures prerequisite data (expirations, etc.) exists before launching feeds.
    """

    def __init__(self, symbol: str, dte_window: int = 10):
        """
        Args:
            symbol (str): The underlying symbol, e.g., "SPX" or "NDX".
            dte_window (int): Max days-to-expiration window to fetch.
        """
        self.symbol = symbol.upper()
        self.expiration_key = REDIS_KEYS["feed_expirations"].format(symbol=self.symbol)
        self.dte_window = dte_window

    def ensure_expirations_cached(self) -> bool:
        """
        Ensure valid expirations exist in Redis for the symbol.
        If missing, fetch them using ExpirationInspector and publish.

        Returns:
            bool: True if expirations are present and cached; False otherwise.
        """
        try:
            cached = redis.get(self.expiration_key)
            if cached:
                expirations = json.loads(cached)
                if expirations:
                    logger.info(
                        f"✅ Cached expirations found for {self.symbol}: {len(expirations)}"
                    )
                    return True
                else:
                    logger.warning(
                        f"⚠️ Cached expirations for {self.symbol} were empty. Refetching..."
                    )

            logger.warning(f"⚠️ No cached expirations found for {self.symbol}, fetching now...")
            inspector = ExpirationInspector(self.symbol, max_dte=self.dte_window)
            inspector.fetch_expirations()

            if not inspector.expirations:
                logger.error(
                    f"🚫 Unable to fetch expirations for {self.symbol}. Feed cannot start."
                )
                return False

            inspector.publish_to_redis()
            logger.info(f"✅ Expirations cached successfully for {self.symbol}")
            return True

        except Exception as e:
            logger.error(
                f"❌ Error ensuring expirations for {self.symbol}: {e}", exc_info=True
            )
            return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m core.feed_bootstrap <SYMBOL>")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    bootstrap = FeedBootstrap(symbol)
    ready = bootstrap.ensure_expirations_cached()
    status = "READY ✅" if ready else "FAILED 🚫"
    print(f"[{symbol}] Feed bootstrap status: {status}")
