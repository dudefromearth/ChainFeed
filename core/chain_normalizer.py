import math
from typing import List, Dict, Optional
import pandas as pd


def normalize_contract(item: Dict) -> Optional[Dict]:
    """Normalize a contract to flat format with required fields."""
    if "details" in item and "last_quote" in item:
        d = item["details"]
        q = item["last_quote"]
        return {
            "ticker": d.get("ticker"),
            "strike": d.get("strike_price"),
            "contract_type": d.get("contract_type"),
            "expiration_date": d.get("expiration_date"),
            "bid": q.get("bid"),
            "ask": q.get("ask")
        }
    elif all(k in item for k in ("ticker", "k", "cp")):
        return {
            "ticker": item.get("ticker"),
            "strike": item.get("k"),
            "contract_type": item.get("cp"),
            "expiration_date": item.get("expiration_date") or item.get("exp"),
            "bid": item.get("q", {}).get("bid"),
            "ask": item.get("q", {}).get("ask")
        }
    return None


def normalize_snapshot(snapshot: Dict) -> List[Dict]:
    contracts = snapshot.get("contracts", [])
    norm = [normalize_contract(c) for c in contracts]
    return [c for c in norm if c and c.get("strike") and c.get("contract_type")]


def estimate_spot(df: pd.DataFrame) -> Optional[float]:
    m = df.dropna(subset=["bid", "ask"]).copy()
    if m.empty:
        return None
    m["mid"] = (m["bid"] + m["ask"]) / 2.0
    calls = m[m["contract_type"] == "call"].groupby("strike")["mid"].median()
    puts  = m[m["contract_type"] == "put"].groupby("strike")["mid"].median()
    K = calls.index.intersection(puts.index)
    if len(K) == 0:
        return None
    syn = [float(k + (calls[k] - puts[k])) for k in K]
    return float(pd.Series(syn).median()) if syn else None


def filter_atm(df: pd.DataFrame, spot: Optional[float], total_strikes: int = 30) -> pd.DataFrame:
    if total_strikes <= 0 or spot is None:
        return df
    strikes = sorted(df["strike"].dropna().unique())
    if not strikes:
        return df
    atm = min(strikes, key=lambda x: abs(x - spot))
    idx = strikes.index(atm)
    half = total_strikes // 2
    lo, hi = max(0, idx - half), min(len(strikes), idx + half)
    window = set(strikes[lo:hi])
    return df[df["strike"].isin(window)]