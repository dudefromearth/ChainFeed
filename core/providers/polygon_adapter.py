#!/usr/bin/env python3
# ===============================================================
# 🌿 PolygonAdapter — Provider Adapter for ChainFeed (v1.1)
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-27
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
# Enhancements:
#   • Reads base_url and api_key from Truth or environment
#   • Explicit logging of configuration source
#   • Cleaner error handling and response validation
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
        """
        Initializes the PolygonAdapter.

        Resolution order:
          1. API key from argument
          2. API key from environment variable (POLYGON_API_KEY)
          3. Base URL from argument
          4. Base URL from environment variable (POLYGON_BASE_URL)
          5. Default fallback to official Polygon snapshot endpoint
        """
        self.logger = logger or logging.getLogger("PolygonAdapter")

        # --- API key resolution ---
        env_api_key = os.getenv("POLYGON_API_KEY")
        self.api_key = api_key or env_api_key
        if not self.api_key:
            self.logger.warning("⚠️  Polygon API key not provided via Truth or environment. API calls will fail.")

        # --- Base URL resolution ---
        env_base_url = os.getenv("POLYGON_BASE_URL")
        self.base_url = base_url or env_base_url or "https://api.polygon.io/v3/snapshot/options"

        self.logger.info(f"🔧 PolygonAdapter initialized → base_url={self.base_url}")

    # -----------------------------------------------------------
    # 🌿 Fetch Chain Snapshot
    # -----------------------------------------------------------
    def fetch_chain_snapshot(self, symbol: str) -> dict:
        """Retrieve live options chain snapshot for a given symbol."""
        url = f"{self.base_url}/{symbol}"
        params = {"apiKey": self.api_key}

        try:
            self.logger.debug(f"🌍 Fetching Polygon chain snapshot: {url}")
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()

            data = resp.json()
            if not isinstance(data, dict):
                raise ValueError(f"Unexpected response type: {type(data)}")

            if "results" not in data and "status" in data and data["status"] != "OK":
                self.logger.warning(f"⚠️ Polygon response missing 'results' field: {data}")
                return {}

            self.logger.debug(f"✅ Received snapshot for {symbol} ({len(data.get('results', []))} results)")
            return data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Polygon API request failed for {symbol}: {e}")
            return {}

        except ValueError as e:
            self.logger.error(f"❌ Polygon response format error for {symbol}: {e}")
            return {}

        except Exception as e:
            self.logger.error(f"❌ Unexpected error fetching chain for {symbol}: {e}", exc_info=True)
            return {}