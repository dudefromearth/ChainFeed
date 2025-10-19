"""
test/test_historical_provider.py
──────────────────────────────────────────────
Unit tests for HistoricalSnapshotProvider:
- Verifies load_snapshot reads local JSON correctly
- Ensures UTC-aware timestamp fields are added
──────────────────────────────────────────────
"""

import os
import json
from datetime import datetime, timezone
from core.providers.historical_provider import HistoricalSnapshotProvider


def test_load_snapshot_from_local(tmp_path):
    """Validate that load_snapshot correctly loads and annotates data."""
    # 1️⃣ Create a temporary sample file
    sample_data = {
        "contracts": [{"details": {"contract_type": "call", "strike_price": 5000}}],
        "symbol": "SPX",
    }

    sample_file = tmp_path / "formatted_SPX_sample.json"
    with open(sample_file, "w") as f:
        json.dump(sample_data, f)

    # 2️⃣ Instantiate provider and load snapshot
    provider = HistoricalSnapshotProvider(symbol="SPX", snapshot_date="2025-10-17")
    loaded = provider.load_snapshot(str(sample_file))

    # 3️⃣ Validate contents
    assert "contracts" in loaded
    assert loaded["symbol"] == "SPX"
    assert loaded["snapshot_date"] == "2025-10-17"
    assert "loaded_at" in loaded

    # 4️⃣ Check timestamp is UTC-aware ISO 8601
    ts = datetime.fromisoformat(loaded["loaded_at"])
    assert ts.tzinfo is not None
    assert ts.tzinfo == timezone.utc

    print("✅ test_load_snapshot_from_local passed.")


if __name__ == "__main__":
    # Direct execution for quick manual verification
    import pytest
    pytest.main([os.path.abspath(__file__)])