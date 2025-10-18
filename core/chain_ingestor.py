# core/chain_ingestor.py

import json
from typing import Dict, Any

def load_chain_from_file(path: str) -> Dict[str, Any]:
    """
    Loads a saved options chain snapshot from local disk.
    Supports:
      - {"contracts": [...]}
      - {"raw": {"contracts": [...]}, "expiration": "..."}
      - {"primary": {...}, "raw": {...}}
    """
    with open(path, "r") as f:
        data = json.load(f)

    # Prefer raw if present
    if "raw" in data and isinstance(data["raw"], dict):
        base = data["raw"]
        expiration = data.get("expiration") or base.get("expiration")
        return {"contracts": base["contracts"], "expiration": expiration}

    # Fallback to primary
    if "primary" in data and isinstance(data["primary"], dict):
        base = data["primary"]
        expiration = data.get("expiration") or base.get("expiration")
        return {"contracts": base["contracts"], "expiration": expiration}

    # Already flat
    if "contracts" in data:
        return {"contracts": data["contracts"], "expiration": data.get("expiration")}

    raise ValueError("Unrecognized snapshot structure")