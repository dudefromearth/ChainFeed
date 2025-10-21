# core/fetch_chain_snapshot.py

import os
import requests
from core.expiration_inspector import ExpirationInspector

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io/v3/snapshot/options"

def fetch_chain_snapshot(symbol: str, dte: int = 0, allow_future: bool = False):
    inspector = ExpirationInspector(symbol)
    inspector.fetch_expirations()

    # Find the valid expiration date
    today = inspector.get_today_str()
    valid_exp = (
        inspector.get_next_valid_expiration(today) if allow_future else
        (today if inspector.is_valid_expiration(today) else None)
    )

    if not valid_exp:
        print(f"❌ No valid expiration for {symbol} on {today}")
        return None

    params = {
        "underlying_asset": symbol,
        "apiKey": POLYGON_API_KEY,
        "days_to_expiration": dte
    }

    try:
        res = requests.get(BASE_URL, params=params)
        res.raise_for_status()
        data = res.json()
        return data.get("results")
    except Exception as e:
        print(f"⚠️ Error fetching chain snapshot for {symbol}: {e}")
        return None