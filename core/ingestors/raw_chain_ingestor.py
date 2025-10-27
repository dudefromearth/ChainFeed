#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Raw Chain Ingestor (v1.1, Truth-Driven)
# ===============================================================
# Fetches live option chain snapshots and publishes to Redis.
#
# Updates:
#   • Integrates Truth-based provider configuration
#   • Passes Polygon base_url and api_key dynamically
#   • Retains all existing logic and threading design
# ===============================================================

import time
import threading
import logging
import os

from core.models.chain_models import ChainRawPayload
from core.ingestors.normalizers.polygon_chain_normalizer import PolygonChainNormalizer
from core.providers.polygon_adapter import PolygonAdapter


class RawChainIngestor(threading.Thread):
    """Fetch → normalize → publish Raw option chain snapshots."""

    def __init__(self, redis_client, truth_cfg, symbol: str, logger: logging.Logger):
        super().__init__(daemon=True)
        self.redis = redis_client
        self.truth_cfg = truth_cfg
        self.symbol = symbol.upper()
        self.logger = logger
        self.running = False

        # --- Runtime parameters from Truth ---
        raw_cfg = (truth_cfg.get("chainfeed") or {}).get("raw", {})
        self.interval = int(raw_cfg.get("interval_sec", 10))
        self.ttl = int(raw_cfg.get("ttl_sec", 3600))

        # --- Provider configuration (Polygon) ---
        polygon_cfg = (
            truth_cfg.get("providers", {})
            .get("data_providers", {})
            .get("polygon_api", {})
        )

        api_key = (
            polygon_cfg.get("api_key")
            or os.getenv(polygon_cfg.get("api_key_env"))
        )
        base_url = polygon_cfg.get("base_url")

        # --- Initialize provider and normalizer ---
        self.normalizer = PolygonChainNormalizer()
        self.adapter = PolygonAdapter(api_key=api_key, base_url=base_url, logger=self.logger)

        # --- Redis key for publishing chain snapshot ---
        self.key = f"truth:chain:raw:{self.symbol}"

        # --- Logging summary for transparency ---
        self.logger.info(
            f"🔧 RawChainIngestor configured for {self.symbol} | "
            f"base_url={base_url or 'default'} | interval={self.interval}s | ttl={self.ttl}s"
        )

    def run(self):
        self.running = True
        self.logger.info(f"🚀 RawChainIngestor started for {self.symbol} (interval={self.interval}s)")

        while self.running:
            try:
                # --- Fetch + normalize + publish ---
                data = self.adapter.fetch_chain_snapshot(self.symbol)
                contracts = self.normalizer.normalize(data)
                payload = ChainRawPayload(
                    symbol=self.symbol,
                    count=len(contracts),
                    contracts=contracts
                )

                json_data = payload.to_json()
                self.redis.setex(self.key, self.ttl, json_data)

                self.logger.info(
                    f"📡 Published Raw chain for {self.symbol} → {self.key} "
                    f"({payload.count} contracts)"
                )

            except Exception as e:
                self.logger.error(f"❌ RawChainIngestor failed for {self.symbol}: {e}", exc_info=True)

            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.logger.info(f"🛑 RawChainIngestor stopped for {self.symbol}")