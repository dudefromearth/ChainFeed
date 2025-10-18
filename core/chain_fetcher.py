import os
import requests
from datetime import datetime, timedelta

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

BASE_URL = "https://api.polygon.io/v3/snapshot/options"

def resolve_expiration(dte: int = 0) -> str:
    """Returns ISO date string for today + dte (trading day assumption)"""
    target = datetime.utcnow() + timedelta(days=dte)
    return target.date().isoformat()


def fetch_option_chain(symbol: str, expiration: str = None) -> dict:
    """Fetches options chain snapshot for a given symbol and expiration date."""
    if POLYGON_API_KEY is None:
        raise EnvironmentError("POLYGON_API_KEY environment variable not set")

    if expiration is None:
        expiration = resolve_expiration(0)

    url = f"{BASE_URL}/{symbol}?expiration_date={expiration}&apiKey={POLYGON_API_KEY}"

    print(f"[~] Fetching chain for {symbol} expiring {expiration}")
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    if "results" not in data:
        raise ValueError(f"No results found in response for {symbol} {expiration}")

    return data["results"]