# utils/expiration_utils.py

from typing import List, Optional
from core.expiration_inspector import ExpirationInspector


def is_valid_expiration(symbol: str, date_str: str) -> bool:
    """Check if a given date is valid for a symbol."""
    inspector = ExpirationInspector(symbol)
    inspector.fetch_expirations()
    return inspector.is_valid_expiration(date_str)


def get_next_valid_expiration(symbol: str, from_date: Optional[str] = None) -> Optional[str]:
    """Return the next valid expiration after a given date (or today if not given)."""
    inspector = ExpirationInspector(symbol)
    inspector.fetch_expirations()
    return inspector.get_next_valid_expiration(from_date)


def list_valid_expirations(symbol: str, max_dte: Optional[int] = None) -> List[str]:
    """List valid expirations for a symbol within max_dte."""
    inspector = ExpirationInspector(symbol, max_dte=max_dte or 10)
    inspector.fetch_expirations()
    return inspector.list_valid_expirations(limit_dte=max_dte)


def summarize_expiration_status(symbol: str, max_dte: Optional[int] = None) -> dict:
    """Summarize expiration availability and metadata for a symbol."""
    inspector = ExpirationInspector(symbol, max_dte=max_dte or 10)
    inspector.fetch_expirations()
    return inspector.summary()