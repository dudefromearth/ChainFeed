"""
core/historical_feed_manager.py
---------------------------------
Manages historical chain feed publication from local files or
Polygon historical API snapshots.

Now supports CLI arguments for group, date, timing, and frequency,
with sensible market-hour defaults.
"""

import argparse
import time
import redis
import warnings
from datetime import datetime, timezone, timedelta
from config.chainfeed_config_loader import load_groups_config
from core.providers.historical_provider import HistoricalSnapshotProvider
from core.chain_ingestor import ChainIngestor


# ─────────────────────────────────────────────
# Redis setup
# ─────────────────────────────────────────────
def connect_redis():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    try:
        r.ping()
        print("✅ Connected to Redis (localhost:6379)")
    except redis.ConnectionError:
        raise SystemExit("❌ Redis is not running. Start it first.")
    return r


# ─────────────────────────────────────────────
# Publishing Logic
# ─────────────────────────────────────────────
def publish_historical_group(group, redis_client):
    """Push all available historical snapshots for this group."""
    print(f"\n📊 Processing group: {group['name']} ({group['key']})")
    ingestor = ChainIngestor()
    group_key = group["key"]
    published = []

    for member in group["members"]:
        symbol = member["symbol"]
        path = member.get("source_path")
        if not path:
            print(f"⚠️ Skipping {symbol} — missing source file path.")
            continue
        try:
            provider = HistoricalSnapshotProvider(symbol)
            snapshot = provider.load_snapshot(path)
            normalized = ingestor.normalize(snapshot)
            if not normalized.get("contracts"):
                raise ValueError("Snapshot missing 'contracts' key for normalization")

            redis_key = f"chain:{group_key}:{symbol}:snapshot"
            redis_client.set(redis_key, str(normalized))
            print(f"✅ Pushed {symbol:<6} → {redis_key}")
            published.append(symbol)
        except Exception as e:
            print(f"❌ Failed to publish {symbol}: {e}")

    if published:
        hb_key = f"heartbeat:{group_key}"
        heartbeat_data = {
            "group": group_key,
            "symbols": published,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        redis_client.set(hb_key, str(heartbeat_data))
        redis_client.expire(hb_key, 60)
        print(f"📡 Heartbeat updated → {hb_key}")
    else:
        print(f"⚠️ No successful symbols in group {group_key}, heartbeat skipped.")


# ─────────────────────────────────────────────
# Time Helpers
# ─────────────────────────────────────────────
def parse_time(value, default):
    """Parse HH:MM strings or return default if blank."""
    if not value:
        return default
    try:
        hour, minute = map(int, value.split(":"))
        return value.replace(":", ":")  # Just to ensure consistency
    except Exception:
        warnings.warn(f"⚠️ Invalid time '{value}', using default {default}")
        return default


def within_market_hours(now, start_time, stop_time):
    """Return True if current time is between start and stop (inclusive)."""
    start = datetime.strptime(start_time, "%H:%M:%S").time()
    stop = datetime.strptime(stop_time, "%H:%M:%S").time()
    return start <= now.time() <= stop


# ─────────────────────────────────────────────
# CLI Entrypoint
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Historical Feed Manager")
    parser.add_argument("--group", help="Group key (e.g., spx_complex)")
    parser.add_argument("--historical-date", help="Date to simulate (YYYY-MM-DD)")
    parser.add_argument("--start-time", help="Start time (HH:MM 24h)")
    parser.add_argument("--stop-time", help="Stop time (HH:MM 24h)")
    parser.add_argument("--frequency", type=int, default=60, help="Frequency in seconds")
    parser.add_argument("--watch", action="store_true", help="Keep watching and publishing")
    parser.add_argument("--interval", type=int, default=60, help="Watch interval (seconds)")
    args = parser.parse_args()

    # ─────────────────────────────────────────────
    # Market-hour defaults
    # ─────────────────────────────────────────────
    start_time = args.start_time or "09:30:01"
    stop_time = args.stop_time or "15:59:59"

    print(f"🕰️  Historical feed window: {start_time} → {stop_time}")

    r = connect_redis()
    groups = load_groups_config()

    selected_group = next((g for g in groups if g["key"] == args.group), None)
    if not selected_group:
        raise SystemExit(f"❌ Group '{args.group}' not found in configuration.")

    print(f"\n📆 Date: {args.historical_date or 'latest available'}")
    print(f"⏱️  Frequency: {args.frequency}s")

    try:
        while True:
            now = datetime.now()
            if within_market_hours(now, start_time, stop_time):
                publish_historical_group(selected_group, r)
            else:
                print(f"⏸️  Outside market hours ({start_time}–{stop_time}), waiting...")
            time.sleep(args.frequency)
    except KeyboardInterrupt:
        print("\n🛑 Feed stopped by user.")


if __name__ == "__main__":
    main()