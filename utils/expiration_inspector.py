import os
import datetime
import requests
from typing import List, Optional
from datetime import timezone

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
BASE_EXPIRATION_URL = "https://api.polygon.io/v3/reference/options/expirations"
BASE_CONTRACT_URL = "https://api.polygon.io/v3/reference/options/contracts"


class ExpirationInspector:
    def __init__(self, symbol: str, max_dte: int = 10):
        self.symbol = symbol.upper()
        self.max_dte = max_dte
        self.expirations: List[str] = []
        self.last_updated: Optional[datetime.datetime] = None

    def get_today_str(self) -> str:
        """Return today's date as an ISO string (YYYY-MM-DD)."""
        return datetime.date.today().isoformat()

    def fetch_expirations(self) -> None:
        """Fetch valid expiration dates from Polygon API or fallback to contract-based inspection."""
        today = self.get_today_str()
        url = f"{BASE_EXPIRATION_URL}?underlying_ticker={self.symbol}&apiKey={POLYGON_API_KEY}&as_of={today}"

        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
            self.expirations = sorted(data.get("results", []))
            if self.expirations:
                self.last_updated = datetime.datetime.now(timezone.utc)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠️ Expiration endpoint failed for {self.symbol}, falling back to contracts...")
                self.expirations = self._derive_expirations_from_contracts(today)
                if self.expirations:
                    self.last_updated = datetime.datetime.now(timezone.utc)
            else:
                print(f"❌ HTTP error while fetching expirations for {self.symbol}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error fetching expirations for {self.symbol}: {e}")

    def _derive_expirations_from_contracts(self, as_of: str) -> List[str]:
        """Fetch options contracts and derive a list of unique expiration dates."""
        url = f"{BASE_CONTRACT_URL}?underlying_ticker={self.symbol}&apiKey={POLYGON_API_KEY}&as_of={as_of}"
        expirations = set()
        try:
            res = requests.get(url)
            res.raise_for_status()
            contracts = res.json().get("results", [])
            print(f"✅ {self.symbol} - Fallback contracts found: {len(contracts)}")
            for contract in contracts[:5]:
                print(f"  • {contract.get('ticker')} -> exp: {contract.get('expiration_date')}")
            for contract in contracts:
                exp = contract.get("expiration_date")
                if exp:
                    expirations.add(exp)
        except Exception as e:
            print(f"❌ Failed to derive expirations from contracts: {e}")
        return sorted(expirations)

    def is_valid_expiration(self, date_str: str) -> bool:
        """Return whether a given ISO date string is a valid expiration."""
        return date_str in self.expirations

    def get_next_valid_expiration(self, from_date: Optional[str] = None, include_today: bool = False) -> Optional[str]:
        """
        Return the next valid expiration after the given date.
        By default, skips today unless include_today=True.
        """
        today = datetime.date.today()
        from_dt = datetime.date.fromisoformat(from_date) if from_date else today

        for exp in self.expirations:
            exp_dt = datetime.date.fromisoformat(exp)
            if exp_dt > from_dt or (include_today and exp_dt == from_dt):
                return exp
        return None

    def list_valid_expirations(self, limit_dte: Optional[int] = None) -> List[str]:
        """Return list of expirations within the max DTE window (default 10)."""
        limit = limit_dte or self.max_dte
        today = datetime.date.today()
        return [
            exp for exp in self.expirations
            if 0 <= (datetime.date.fromisoformat(exp) - today).days <= limit
        ]

    def summary(self) -> dict:
        """Return a summary dict with metadata."""
        return {
            "symbol": self.symbol,
            "valid_expirations": self.list_valid_expirations(),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }