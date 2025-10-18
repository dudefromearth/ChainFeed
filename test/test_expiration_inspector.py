# Put this at the top
from utils.expiration_inspector import ExpirationInspector

VALID_SYMBOL = "SPX"
INVALID_SYMBOL = "FAKESYMBOL"

# 👇 This test uses a known valid symbol
def test_fetch_expirations_runs_and_returns_list():
    inspector = ExpirationInspector(VALID_SYMBOL)
    inspector.fetch_expirations()
    assert isinstance(inspector.expirations, list)
    assert len(inspector.expirations) > 0, "Should return some expirations"

def test_is_valid_expiration_with_known_date():
    inspector = ExpirationInspector(VALID_SYMBOL)
    inspector.fetch_expirations()
    known = inspector.expirations[0]
    assert inspector.is_valid_expiration(known) is True

def test_next_valid_expiration():
    inspector = ExpirationInspector(VALID_SYMBOL)
    inspector.fetch_expirations()

    today = inspector.get_today_str()
    next_exp = inspector.get_next_valid_expiration()
    if next_exp is None:
        next_exp = inspector.get_next_valid_expiration(include_today=True)

    assert next_exp is not None, "Should return today's expiration when include_today=True"

# ✅ New test for invalid input
def test_invalid_symbol_fails_gracefully():
    inspector = ExpirationInspector(INVALID_SYMBOL)
    inspector.fetch_expirations()

    assert inspector.expirations == [], "Should return an empty list for an invalid symbol"
    assert inspector.last_updated is None, "last_updated should remain None on failure"