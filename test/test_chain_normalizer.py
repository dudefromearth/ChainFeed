# test/test_chain_normalizer.py

import pytest
import json
from pathlib import Path
from core.chain_normalizer import normalize_snapshot

# ✅ Use the correct relative path to the fixture
FIXTURE_FILE = Path(__file__).parents[1] / "data" / "formatted.json"


def test_normalize_snapshot_loads_and_parses_correctly():
    """Ensure that a formatted chain snapshot normalizes into the correct list structure."""
    assert FIXTURE_FILE.exists(), f"Fixture file not found: {FIXTURE_FILE}"

    with open(FIXTURE_FILE, "r") as f:
        raw_data = json.load(f)

    result = normalize_snapshot(raw_data)

    # ✅ Must return a list
    assert isinstance(result, list), "normalize_snapshot() should return a list of contracts"
    assert len(result) > 0, "Should contain at least one contract"

    # ✅ Validate one sample contract
    sample = result[0]
    required_fields = ["ticker", "strike", "contract_type", "expiration_date", "bid", "ask"]
    for field in required_fields:
        assert field in sample, f"Contract missing field: {field}"

    # ✅ Optional checks for value types
    assert isinstance(sample["ticker"], str)
    assert isinstance(sample["strike"], (int, float))
    assert isinstance(sample["contract_type"], str)
    assert isinstance(sample["expiration_date"], str)
    assert isinstance(sample["bid"], (int, float))
    assert isinstance(sample["ask"], (int, float))