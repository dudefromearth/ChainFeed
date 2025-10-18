# test/test_snapshot_providers.py

from core.providers.synthetic_snapshot_provider import SyntheticSnapshotProvider

REQUIRED_FIELDS = {"ticker", "strike", "contract_type", "expiration_date", "bid", "ask"}

def test_synthetic_provider_returns_expected_data():
    """
    Synthetic provider should return a well-formed, mock snapshot for development and testing.
    """
    provider = SyntheticSnapshotProvider("TEST")
    snapshot = provider.fetch_chain_snapshot()

    assert isinstance(snapshot, dict), "Snapshot should be a dictionary"
    assert snapshot.get("symbol") == "TEST"
    assert snapshot.get("generated") is True

    contracts = snapshot.get("contracts")
    assert isinstance(contracts, list), "'contracts' should be a list"
    assert len(contracts) == 2, "Expected exactly 2 mock contracts"

    for contract in contracts:
        missing = REQUIRED_FIELDS - set(contract.keys())
        assert not missing, f"Contract is missing required fields: {missing}"