"""
Quick inspection tool for verifying HistoricalSnapshotProvider output.
"""

from core.providers.historical_provider import HistoricalSnapshotProvider
import json
import pprint

def main():
    symbol = "SPX"
    path = "data/formatted.json"

    print(f"\n🔍 Inspecting snapshot for {symbol} at {path}\n")

    provider = HistoricalSnapshotProvider(symbol)
    snapshot = provider.load_snapshot(path)

    # Print the object type
    print(f"Type: {type(snapshot)}")

    # If it's a dict, show keys
    if isinstance(snapshot, dict):
        print(f"Keys: {list(snapshot.keys())[:10]}")
        if "contracts" in snapshot:
            print(f"Contracts count: {len(snapshot['contracts'])}")
    elif isinstance(snapshot, list):
        print(f"List length: {len(snapshot)} (likely raw contracts)")

    # Optional: show first contract for inspection
    print("\n--- Sample Data ---")
    pprint.pprint(snapshot[:1] if isinstance(snapshot, list) else snapshot.get('contracts', [])[:1])

    # Optional: save a clean version to verify structure
    with open("snapshot_debug.json", "w") as f:
        json.dump(snapshot, f, indent=2)
        print("\n✅ Wrote snapshot_debug.json for review.\n")

if __name__ == "__main__":
    main()
