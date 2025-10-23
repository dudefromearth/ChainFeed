"""
core/feed_monitor.py
--------------------

Feed Monitor (Passive Subscription Observer)
--------------------------------------------
Subscribes to configured feeds from Redis Pub/Sub
based on runtime config (`config/variant_config.yaml`).

Tracks message freshness and reports health live.
"""

import os
import json
import signal
import time
import yaml
import threading
from datetime import datetime, timezone
from utils.logger import get_logger
from utils.redis_client import get_redis_client
from config.chainfeed_constants import REDIS_PREFIX

logger = get_logger("feed.monitor")
redis = get_redis_client()


class FeedMonitor:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._resolve_config_path()
        self.running = True
        self.last_update = {}  # {channel: timestamp}
        self.subscribed_channels = []
        self.refresh_interval = 5  # seconds
        self.pubsub = None

        self.config = self._load_config()
        self.subscribed_channels = self._build_channel_list()

        logger.info(f"🧠 FeedMonitor initialized with {len(self.subscribed_channels)} channels.")
        if not self.subscribed_channels:
            logger.warning("⚠️ No active feed channels found in config.")

    # ----------------------------------------------------------
    # CONFIG
    # ----------------------------------------------------------
    def _resolve_config_path(self):
        """Find config/variant_config.yaml relative to project root."""
        cwd = os.getcwd()
        candidate = os.path.join(cwd, "config", "variant_config.yaml")
        if os.path.exists(candidate):
            return candidate
        alt = os.path.join(os.path.dirname(__file__), "../config/variant_config.yaml")
        return os.path.abspath(alt)

    def _load_config(self) -> dict:
        """Read YAML config file and return parsed dictionary."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"📖 Loaded config from {self.config_path}")
            return config or {}
        except Exception as e:
            logger.error(f"❌ Failed to load config file {self.config_path}: {e}")
            return {}

    def _build_channel_list(self):
        """Extract all enabled feeds from YAML config."""
        feeds = self.config.get("feeds", {})
        channels = []
        for group, meta in feeds.items():
            if not meta.get("enabled", False):
                continue
            for sym in meta.get("symbols", []):
                channels.append(f"{REDIS_PREFIX}:{sym}:full")
                channels.append(f"{REDIS_PREFIX}:{sym}:diff")
        return sorted(set(channels))

    # ----------------------------------------------------------
    # SUBSCRIPTION
    # ----------------------------------------------------------
    def _handle_message(self, channel, message):
        """Handle incoming Redis Pub/Sub messages."""
        self.last_update[channel] = time.time()
        logger.debug(f"📡 Update received on {channel}")

    def _subscribe_sync(self):
        """Blocking Redis subscription loop (in background thread)."""
        try:
            self.pubsub = redis.pubsub(ignore_subscribe_messages=True)
            self.pubsub.subscribe(*self.subscribed_channels)
            logger.info(f"📡 Subscribed to {len(self.subscribed_channels)} channels.")

            for msg in self.pubsub.listen():
                if not self.running:
                    break
                if msg["type"] == "message":
                    self._handle_message(msg["channel"].decode(), msg["data"])
        except Exception as e:
            logger.error(f"❌ Subscription thread error: {e}")

    # ----------------------------------------------------------
    # MONITOR LOOP
    # ----------------------------------------------------------
    def _report_health(self):
        """Continuously print live feed health table."""
        while self.running:
            now = time.time()
            os.system("clear")
            print("🩺 Feed Health Summary")
            print("----------------------------------------------------------")

            if not self.subscribed_channels:
                print("⚠️ No active feeds configured.")
            else:
                for ch in self.subscribed_channels:
                    last = self.last_update.get(ch)
                    age = now - last if last else None
                    if age is None:
                        status = "🟡 pending"
                    elif age < 5:
                        status = "🟢 healthy"
                    elif age < 15:
                        status = "🟠 slow"
                    else:
                        status = "🔴 stale"
                    print(f"{ch:<45} {status:<10} {age if age else '—':>6}")

            print("----------------------------------------------------------")
            time.sleep(self.refresh_interval)

    # ----------------------------------------------------------
    # RUNTIME CONTROL
    # ----------------------------------------------------------
    def run(self):
        """Run the monitor."""
        logger.info("🚀 FeedMonitor started.")

        if self.subscribed_channels:
            thread = threading.Thread(target=self._subscribe_sync, daemon=True)
            thread.start()

        try:
            self._report_health()
        except KeyboardInterrupt:
            self.stop()

    def stop(self, *_):
        """Gracefully stop monitor."""
        logger.warning("🛑 FeedMonitor shutdown requested.")
        self.running = False
        if self.pubsub:
            try:
                self.pubsub.close()
            except Exception:
                pass


if __name__ == "__main__":
    monitor = FeedMonitor()
    signal.signal(signal.SIGINT, monitor.stop)
    signal.signal(signal.SIGTERM, monitor.stop)
    monitor.run()