"""
core/chain_ingestor.py
──────────────────────────────────────────────
Handles ingestion and normalization of chain snapshots
from local or historical data sources.

Now robust against both:
  • snapshot dicts: {"contracts": [...]}
  • raw lists of contract dicts: [...]
──────────────────────────────────────────────
"""

import json
from typing import Any, Dict, List


class ChainIngestor:
    """Responsible for validating and normalizing chain snapshots."""

    def normalize(self, snapshot: Any) -> Dict[str, Any]:
        """
        Normalize a raw or structured snapshot into a standard format.
        """

        # --- Handle list input directly ---
        if isinstance(snapshot, list):
            return {"contracts": snapshot, "normalized": True}

        # --- Handle dict snapshots with embedded contracts ---
        if isinstance(snapshot, dict):
            if "contracts" in snapshot:
                return {
                    "contracts": snapshot["contracts"],
                    "metadata": {
                        k: v for k, v in snapshot.items() if k != "contracts"
                    },
                    "normalized": True,
                }

            # Some providers might use alternate key names
            if "results" in snapshot:
                return {"contracts": snapshot["results"], "normalized": True}

        raise ValueError("Snapshot missing 'contracts' key for normalization")


# ──────────────────────────────────────────────
# Utility for loading local files directly
# ──────────────────────────────────────────────

def load_chain_from_file(path: str) -> Dict[str, Any]:
    """
    Loads a saved options chain snapshot from disk.
    Supports multiple formats:
      - {"contracts": [...]}
      - {"raw": {"contracts": [...]}, "expiration": "..."}
      - {"primary": {...}, "raw": {...}}
    """
    with open(path, "r") as f:
        data = json.load(f)

    if "raw" in data and isinstance(data["raw"], dict):
        base = data["raw"]
        expiration = data.get("expiration") or base.get("expiration")
        return {"contracts": base["contracts"], "expiration": expiration}

    if "primary" in data and isinstance(data["primary"], dict):
        base = data["primary"]
        expiration = data.get("expiration") or base.get("expiration")
        return {"contracts": base["contracts"], "expiration": expiration}

    if "contracts" in data:
        return {"contracts": data["contracts"], "expiration": data.get("expiration")}

    raise ValueError("Unrecognized snapshot structure")