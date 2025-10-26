#!/usr/bin/env python3
# ===============================================================
# 🌿 PolygonAdapter — Provider Adapter for ChainFeed
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Provides a provider-independent interface for fetching options
# chain snapshots from Polygon.io. Implements the ProviderAdapter
# base interface used by all feed workers.
#
# Design:
#   • Adapter Pattern — abstracts Polygon-specific API details.
#   • Supports easy substitution of future providers (Orats, IBKR).
#   • Configured by environment variables or Truth schema.
#
# Redis integration occurs in FeedWorker, not here.
# ===============================================================

import os
import requests
import logging


class ProviderAdapter:
    """Abstract base adapter for all data providers."""
    def fetch_chain_snapshot(self, symbol: str) -> dict:
        raise NotImplementedError


class PolygonAdapter(ProviderAdapter):
    """Fetches real-time options chain snapshots from Polygon.io."""

    def __init__(self, api_key: str = None, base_url: str = None, logger: logging.Logger = None):
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        self.base_url = base_url or "https://api.polygon.io/v3/snapshot/options"
        self.logger = logger or logging.getLogger("PolygonAdapter")

        if not self.api_key:
            self.logger.warning("⚠️  POLYGON_API_KEY not set — API calls will fail.")

    # -----------------------------------------------------------
    # 🌿 Fetch Chain Snapshot
    # -----------------------------------------------------------
    def fetch_chain_snapshot(self, symbol: str) -> dict:
        """Retrieve live options chain snapshot for a given symbol."""
        url = f"{self.base_url}/{symbol}"
        params = {"apiKey": self.api_key}

        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise ValueError("Unexpected response type from Polygon.")
            return data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Polygon API request failed for {symbol}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"❌ Unexpected error fetching chain for {symbol}: {e}", exc_info=True)
            return {}