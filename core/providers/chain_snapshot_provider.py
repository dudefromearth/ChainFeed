#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainSnapshotProvider — Abstract Base Provider for ChainFeed
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-27
#
# Purpose:
# --------
# Defines a unified interface for fetching option chain snapshots,
# abstracting away provider-specific APIs (Polygon, Orats, Tradier, etc.).
#
# Design Pattern:
#   • Strategy pattern — each provider (PolygonAdapter, OratsAdapter, etc.)
#     implements the same interface and can be swapped dynamically.
# ===============================================================

import abc
from typing import Dict, Any


class ChainSnapshotProvider(abc.ABC):
    """Abstract interface for real-time option chain snapshot providers."""

    @abc.abstractmethod
    def fetch_chain_snapshot(self, symbol: str) -> Dict[str, Any]:
        """Retrieve a full chain snapshot for the given symbol."""
        raise NotImplementedError("Provider must implement fetch_chain_snapshot()")