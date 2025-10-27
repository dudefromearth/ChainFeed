#!/usr/bin/env python3
# ===============================================================
# 🌿 PolygonChainFetcher – Provider Adapter for ChainFeed
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-27
#
# Purpose:
# --------
# Fetches raw, full, or diff option chain snapshots from Polygon.io
# and instantiates canonical ChainFeed objects.
#
# Design:
#   • Uses the ChainFetcher interface
#   • Provider-agnostic beyond this layer
#   • Returns self-serializing ChainFeed objects
# ===============================================================

import os
import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from core.interfaces.chain_fetcher import ChainFetcher
from core.models.chain_models import ChainFeed, OptionContract


class PolygonChainFetcher(ChainFetcher):
    """Concrete fetcher that retrieves and transforms data from Polygon.io."""

    BASE_URL = "https://api.polygon.io/v3/snapshot/options"

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.api_key = os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            self.logger.warning("⚠️ POLYGON_API_KEY not set — Polygon fetches will fail.")

    # -----------------------------------------------------------
    # 🧩 Provider Identity
    # -----------------------------------------------------------
    @property
    def provider(self) -> str:
        return "Polygon.io"

    # -----------------------------------------------------------
    # 🌐 Low-level Fetch
    # -----------------------------------------------------------
    def get_raw_data(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP GET request to Polygon."""
        params["apiKey"] = self.api_key
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Polygon API error: {e}")
            return {}

    # -----------------------------------------------------------
    # 🌿 High-level Chain Fetch
    # -----------------------------------------------------------
    def fetch(self, symbol: str, mode: str = "raw") -> ChainFeed:
        """
        Fetch option chain data from Polygon.io and instantiate a canonical ChainFeed.
        The 'mode' is advisory — it affects the endpoint path, not the object model.
        """
        endpoint = f"{self.BASE_URL}/{symbol.upper()}"
        raw_data = self.get_raw_data(endpoint, {})

        if not raw_data or "results" not in raw_data:
            self.logger.warning(f"⚠️ No data returned for {symbol}.")
            return ChainFeed(symbol=symbol, source=self.provider, count=0, contracts=[])

        # Extract normalized contracts
        options = raw_data.get("results", {}).get("options", [])
        contracts: List[OptionContract] = []

        for opt in options:
            details = opt.get("details", {})
            greeks = opt.get("greeks", {})
            quote = opt.get("last_quote", {})
            day = opt.get("day", {})

            try:
                contract = OptionContract(
                    contract_type=details.get("contract_type", "").lower(),
                    strike=details.get("strike_price", 0.0),
                    expiry=details.get("expiration_date", ""),
                    bid=quote.get("bid"),
                    ask=quote.get("ask"),
                    mark=(quote.get("bid", 0) + quote.get("ask", 0)) / 2 if quote.get("ask") else None,
                    iv=greeks.get("iv"),
                    delta=greeks.get("delta"),
                    gamma=greeks.get("gamma"),
                    theta=greeks.get("theta"),
                    vega=greeks.get("vega"),
                    oi=details.get("open_interest"),
                    volume=day.get("volume"),
                )
                contracts.append(contract)
            except Exception as e:
                self.logger.error(f"⚠️ Error parsing contract for {symbol}: {e}")

        chain_feed = ChainFeed(
            symbol=symbol,
            source=self.provider,
            count=len(contracts),
            contracts=contracts,
            metadata={
                "mode": mode,
                "provider_endpoint": endpoint,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        self.logger.info(f"📦 {symbol} → {len(contracts)} contracts fetched from Polygon.io")

        return chain_feed