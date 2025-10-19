"""
Tests the interface between HistoricalSnapshotProvider and ChainIngestor
for multiple symbols (e.g., SPX and ES). Falls back to local data when
POLYGON_API_KEY is not set.
"""

import os
import sys
import json
import pprint
import warnings

# --- Ensure project root is on sys.path for local execution ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.providers.historical_provider import HistoricalSnapshotProvider
from core.chain_ingestor import ChainIngestor

# Local offline samples
LOCAL_SAMPLES = {
    "SPX": os.path.join(PROJECT_ROOT, "data", "formatted.json"),
    "ES": os.path.join(PROJECT_ROOT, "data", "formatted_ES.json"),  # add this sample file
}


def run_symbol(symbol: str, expiration: str, snapshot_date: str):
    """
    Runs a single HistoricalSnapshotProvider → ChainIngestor test.
    """
    print(f"\n==================== {symbol} ====================")

    api_key = os.getenv("POLYGON_API_KEY")
    snapshot = None

    if not api_key:
        warnings.warn(
            f"⚠️ POLYGON_API_KEY not set. Falling back to local file for {symbol}.",
            category=UserWarning
        )
        local_path = LOCAL_SAMPLES.get(symbol)
        if not local_path or not os.path.exists(local_path):
            print(f"❌ No local file found for {symbol}: {local_path}")
            return
        with open(local_path, "r") as f:
            snapshot = json.load(f)
    else:
        provider = HistoricalSnapshotProvider(
            symbol=symbol,
            expiration=expiration,
            snapshot_date=snapshot_date,
        )
        snapshot = provider.fetch_chain_snapshot()

    if not snapshot:
        print(f"⚠️ No snapshot returned for {symbol}.")
        return

    print("\n--- RAW HISTORICAL SNAPSHOT ---")
    pprint.pprint(snapshot if isinstance(snapshot, dict) else snapshot[:1])

    ingestor = ChainIngestor()
    try:
        normalized = ingestor.normalize(snapshot)
    except Exception as e:
        print(f"❌ Ingestor failed to normalize {symbol}: {e}")
        return

    print("\n--- NORMALIZED CHAIN (INGESTED) ---")
    pprint.pprint(normalized)
    print("\n--- JSON ---")
    print(json.dumps(normalized, indent=2))


def main():
    tests = [
        {"symbol": "SPX", "expiration": "2025-10-17", "snapshot_date": "2025-10-18"},
        {"symbol": "ES", "expiration": "2025-10-17", "snapshot_date": "2025-10-18"},
    ]

    for t in tests:
        run_symbol(**t)


if __name__ == "__main__":
    main()