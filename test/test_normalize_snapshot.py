from core.chain_ingestor import ChainIngestor
from core.providers.historical_provider import HistoricalSnapshotProvider
import pprint

def main():
    symbol = "SPX"
    path = "data/formatted.json"

    provider = HistoricalSnapshotProvider(symbol)
    snapshot = provider.load_snapshot(path)
    contracts = snapshot.get("contracts", snapshot)

    print(f"\nLoaded {len(contracts)} contracts for {symbol}")

    ingestor = ChainIngestor()
    try:
        normalized = ingestor.normalize(contracts)
        print("\n--- Normalized sample ---")
        pprint.pprint(normalized if isinstance(normalized, dict) else normalized[:1])
    except Exception as e:
        print(f"❌ Normalization failed: {e}")

if __name__ == "__main__":
    main()