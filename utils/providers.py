# utils/providers.py
import os
import requests
import datetime
from typing import Protocol, Optional

from core.chain_normalizer import normalize_snapshot

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

class ChainSnapshotProvider(Protocol):
    def fetch(self, symbol: str, **kwargs) -> Optional[dict]:
        ...


class LivePolygonProvider:
    def fetch(self, symbol: str, dte: int = 0) -> Optional[dict]:
        url = (
            f"https://api.polygon.io/v3/snapshot/options"
            f"?underlying_asset={symbol}&days_to_expiration={dte}&apiKey={POLYGON_API_KEY}"
        )
        try:
            res = requests.get(url)
            res.raise_for_status()
            return res.json().get("results")
        except Exception as e:
            print(f"❌ Live fetch failed for {symbol}: {e}")
            return None


class HistoricalPolygonProvider:
    def fetch(self, symbol: str, date: str) -> Optional[dict]:
        url = (
            f"https://api.polygon.io/v3/snapshot/options"
            f"?underlying_asset={symbol}&as_of={date}&apiKey={POLYGON_API_KEY}"
        )
        try:
            res = requests.get(url)
            res.raise_for_status()
            return res.json().get("results")
        except Exception as e:
            print(f"❌ Historical fetch failed for {symbol} on {date}: {e}")
            return None


# Generic ingestion function
def ingest_chain(provider: ChainSnapshotProvider, symbol: str, **kwargs):
    raw = provider.fetch(symbol, **kwargs)
    if not raw:
        print(f"⚠️ No data fetched for {symbol}")
        return
    normalized = normalize_snapshot(raw)
    print(f"✅ Ingested and normalized {symbol} - {len(normalized['contracts'])} contracts")
    # Here you'd normally publish to DB or queue
    return normalized