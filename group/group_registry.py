# core/group_registry.py
import yaml
from typing import List, Dict, Optional

class GroupRegistry:
    """
    Central registry for all ChainFeed groups.
    Each group defines a set of correlated instruments (feeds) and their relationships.
    """

    def __init__(self, path: str = "groups.yaml"):
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        self.groups = data.get("groups", [])

    def list_groups(self) -> List[str]:
        """Return list of all group keys."""
        return [g["key"] for g in self.groups]

    def get_group(self, key: str) -> Optional[Dict]:
        """Return full group definition for a given key."""
        return next((g for g in self.groups if g["key"] == key), None)

    def get_symbols(self, key: str) -> List[str]:
        """Return list of member symbols for a given group key."""
        group = self.get_group(key)
        return [m["symbol"] for m in group.get("members", [])] if group else []

    def get_cross_pairs(self, key: str) -> List[List[str]]:
        """Return defined cross-pairs for a group (if any)."""
        group = self.get_group(key)
        return group.get("cross_pairs", []) if group else []

    def all_symbols(self) -> List[str]:
        """Flatten and return all unique symbols across all groups."""
        syms = set()
        for g in self.groups:
            for m in g.get("members", []):
                syms.add(m["symbol"])
        return sorted(list(syms))