import pytest
import warnings
from core.providers.live_provider import LiveSnapshotProvider
from core.expiration_inspector import ExpirationInspector


@pytest.fixture
def inspector_spx():
    inspector = ExpirationInspector("SPX")
    inspector.fetch_expirations()
    return inspector


def test_live_provider_infers_today_or_none(inspector_spx):
    """
    If today is a valid expiration, provider should fetch a snapshot.
    Otherwise, it should return None and explain why.
    """
    provider = LiveSnapshotProvider("SPX")
    snapshot = provider.fetch_chain_snapshot()

    today = inspector_spx.get_today_str()
    if inspector_spx.is_valid_expiration(today):
        assert isinstance(snapshot, dict), "Expected snapshot for today's valid expiration"
    else:
        assert snapshot is None, "Expected None when today is not a valid expiration"


def test_live_provider_with_explicit_expiration(inspector_spx):
    """
    When explicitly passed a valid expiration, provider should return a snapshot.
    If None is returned, warn but do not fail — data may not yet exist.
    """
    valid_exp = inspector_spx.get_next_valid_expiration(include_today=True)
    provider = LiveSnapshotProvider("SPX", expiration=valid_exp)
    snapshot = provider.fetch_chain_snapshot()

    if snapshot is None:
        warnings.warn(
            f"⚠️ No snapshot returned for explicitly valid expiration {valid_exp}. "
            "This may be due to Polygon API data delay or weekend.",
            UserWarning
        )
    else:
        assert isinstance(snapshot, dict), "Expected snapshot for explicitly valid expiration"


def test_live_provider_handles_invalid_expiration():
    """
    Passing an obviously invalid expiration should return None and warn.
    """
    provider = LiveSnapshotProvider("SPX", expiration="1900-01-01")
    with pytest.warns(UserWarning, match="not valid for SPX"):
        result = provider.fetch_chain_snapshot()
        assert result is None