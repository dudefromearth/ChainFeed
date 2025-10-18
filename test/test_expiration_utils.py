# test/test_expiration_utils.py

import pytest
from utils.expiration_utils import (
    is_valid_expiration,
    get_next_valid_expiration,
    list_valid_expirations,
    summarize_expiration_status
)

SYMBOL = "SPX"

def test_summarize_expiration_status():
    summary = summarize_expiration_status(SYMBOL, max_dte=10)
    assert "symbol" in summary
    assert summary["symbol"] == SYMBOL
    assert isinstance(summary["valid_expirations"], list)
    assert summary["last_updated"] is None or isinstance(summary["last_updated"], str)

def test_list_valid_expirations():
    expirations = list_valid_expirations(SYMBOL, max_dte=10)
    assert isinstance(expirations, list)

def test_get_next_valid_expiration():
    next_exp = get_next_valid_expiration(SYMBOL)
    assert next_exp is None or isinstance(next_exp, str)

def test_is_valid_expiration():
    expirations = list_valid_expirations(SYMBOL, max_dte=10)
    if expirations:
        assert is_valid_expiration(SYMBOL, expirations[0]) is True