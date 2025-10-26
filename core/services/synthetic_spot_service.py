#!/usr/bin/env python3
# ===============================================================
# 🌿 SyntheticSpotService — SPX_synth & NDX_synth Generator
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Combines ETF and Futures data (SPY+ES, QQQ+NQ)
# using configurable multipliers and weights to derive
# synthetic index spot prices, even when live data is unavailable.
#
# Enhancements:
#   • Integrated MarketStateValidator for context-aware validation.
#   • Prevents computation during closed markets or invalid sessions.
#   • Publishes descriptive validation messages to Redis.
#
# Publishes:
#   truth:spot:SPX_synth
#   truth:spot:NDX_synth
#   truth:feed:{symbol}:validation
# ===============================================================

import time
import json
import threading
import logging
from datetime import datetime, timezone

from core.startup.services.market_state_validator import MarketStateValidator


class SyntheticSpotService:
    def __init__(self, redis_client, truth_cfg, logger=None, interval_sec=10):
        self.redis = redis_client
        self.truth = truth_cfg
        self.logger = logger or logging.getLogger("SyntheticSpotService")
        self.interval = interval_sec
        self.running = False

        # Retrieve synthetic configuration from canonical truth
        self.synthetics = truth_cfg["chainfeed"]["synthetic_indexes"]

        # Inject market state validation
        self.market_validator = MarketStateValidator(
            redis_client=self.redis, logger=self.logger
        )

    # -----------------------------------------------------------
    def start(self):
        """Start the service in a background thread."""
        self.running = True
        t = threading.Thread(target=self.run, daemon=True)
        t.start()
        self.logger.info("🧮 SyntheticSpotService started.")

    def stop(self):
        self.running = False
        self.logger.info("🧮 SyntheticSpotService stopped.")

    # -----------------------------------------------------------
    def run(self):
        """Main loop for computing synthetic spot indexes."""
        while self.running:
            try:
                for synth_name, cfg in self.synthetics.items():
                    # Validate feed context before computation
                    valid, reason = self.market_validator.validate_feed_availability(synth_name)
                    if not valid:
                        self.logger.info(f"🕊️ [{synth_name}] Skipped: {reason}")
                        continue

                    components = cfg["components"]
                    total = 0.0
                    missing = []

                    # Aggregate synthetic value from components
                    for comp in components:
                        price = self._get_price(comp["symbol"])
                        if price is None:
                            missing.append(comp["symbol"])
                            continue
                        total += price * comp["weight"] * comp["multiplier"]

                    # Handle missing component data
                    if missing:
                        self._publish_validation(
                            synth_name,
                            "partial",
                            f"Missing component data for: {', '.join(missing)}",
                        )
                        self.logger.warning(
                            f"⚠️ [{synth_name}] Missing component data for {', '.join(missing)}"
                        )
                        continue

                    # Publish computed synthetic spot
                    if total > 0:
                        self._publish_spot(synth_name, total)
                        self.logger.info(f"✅ [{synth_name}] Synthetic spot {total:.2f}")

            except Exception as e:
                self.logger.error(f"❌ Synthetic spot computation error: {e}", exc_info=True)

            time.sleep(self.interval)

    # -----------------------------------------------------------
    def _get_price(self, symbol: str):
        """Fetch the latest price (live or historical) from Redis."""
        try:
            key = f"truth:feed:{symbol}:snapshot"
            raw = self.redis.get(key)
            if not raw:
                return None
            data = json.loads(raw)
            return data.get("spot")
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve price for {symbol}: {e}", exc_info=True)
            return None

    # -----------------------------------------------------------
    def _publish_spot(self, synth_name: str, value: float):
        """Publish the computed synthetic spot value."""
        ts = datetime.now(timezone.utc).isoformat()
        payload = {
            "timestamp": ts,
            "symbol": synth_name,
            "spot": round(value, 2),
            "source": "synthetic",
        }
        key = f"truth:spot:{synth_name}"
        self.redis.set(key, json.dumps(payload))
        self.redis.expire(key, 15)
        self._publish_validation(synth_name, "ok", "Synthetic computation successful.")

    # -----------------------------------------------------------
    def _publish_validation(self, symbol: str, state: str, message: str):
        """Publish validation state for this synthetic feed."""
        try:
            key = f"truth:feed:{symbol}:validation"
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "state": state,
                "message": message,
            }
            self.redis.set(key, json.dumps(payload))
        except Exception as e:
            self.logger.warning(f"⚠️ Could not publish validation status for {symbol}: {e}")