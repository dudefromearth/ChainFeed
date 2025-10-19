"""
core/historical_feed_manager.py
──────────────────────────────────────────────
Coordinates historical snapshot ingestion, normalization,
and publication to Redis. Emits heartbeats per group.

Fully hardened:
  - Auto source_path fallback
  - Resilient error handling
  - Redis TTL heartbeats
  - Correct contract passing to ChainIngestor
──────────────────────────────────────────────
"""

import os
import json
import time
import yaml
import redis
from datetime import datetime, timezone
from core.providers.historical_provider import HistoricalSnapshotProvider
from core.chain_ingestor import ChainIngestor


# ──────────────────────────────────────────────
# Redis setup
# ──────────────────────────────────────────────

def get_redis_client() -> redis.Redis:
    """Connect to local Redis."""
    try:
        client = redis.Redis(host="localhost", port=6379, db=0)
        client.ping()
        print("✅ Connected to Redis (localhost:6379)")
        return client
    except redis.ConnectionError as e:
        raise RuntimeError(f"❌ Cannot connect to Redis: {e}")


# ──────────────────────────────────────────────
# Config loader
# ──────────────────────────────────────────────

def load_groups_config(path: str = None):
    """Load YAML group configuration from project root."""
    if path is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(base_dir, "groups.yaml")

    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Missing groups.yaml at {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f)["groups"]


# ──────────────────────────────────────────────
# Core publishing logic
# ──────────────────────────────────────────────

def publish_historical_group(group: dict, redis_client: redis.Redis):
    """Publish normalized historical chains for one group."""
    ingestor = ChainIngestor()
    group_key = group["key"]
    members = group["members"]
    heartbeat_key = group["heartbeat_key"]

    print(f"\n📊 Processing group: {group['name']} ({group_key})")

    published_symbols = []

    for member in members:
        symbol = member["symbol"]
        expiration = member.get("expiration")
        source_path = member.get("source_path") or f"data/formatted_{symbol}.json"

        if not os.path.exists(source_path):
            print(f"⚠️ Skipping {symbol} — missing source file: {source_path}")
            continue

        try:
            provider = HistoricalSnapshotProvider(symbol, expiration)
            snapshot = provider.load_snapshot(source_path)

            # --- Intelligent structure detection ---
            if isinstance(snapshot, dict):
                if "contracts" in snapshot:
                    contracts = snapshot["contracts"]
                elif "results" in snapshot:
                    contracts = snapshot["results"]
                else:
                    raise ValueError("Snapshot missing 'contracts' or 'results' key")
            elif isinstance(snapshot, list):
                contracts = snapshot
            else:
                raise TypeError(f"Unexpected snapshot type: {type(snapshot)}")

            normalized = ingestor.normalize(contracts)

            # Add metadata back to normalized chain
            normalized["symbol"] = symbol
            normalized["expiration"] = expiration
            normalized["published_at"] = datetime.now(timezone.utc).isoformat()

            # Push to Redis
            redis_key = f"chain:{group_key}:{symbol}:snapshot"
            redis_client.set(redis_key, json.dumps(normalized))
            published_symbols.append(symbol)

            print(f"✅ Pushed {symbol:<6} → {redis_key}")

        except Exception as e:
            print(f"❌ Failed to publish {symbol}: {e}")

    # Emit group heartbeat if any member succeeded
    if published_symbols:
        heartbeat_data = {
            "group": group_key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbols": published_symbols,
        }
        redis_client.setex(heartbeat_key, 60, json.dumps(heartbeat_data))
        print(f"📡 Heartbeat updated → {heartbeat_key}")
    else:
        print(f"⚠️ No successful symbols in group {group_key}, heartbeat skipped.")


# ──────────────────────────────────────────────
# Run all configured groups
# ──────────────────────────────────────────────

def run_all_groups():
    """Run the full feed cycle for all configured groups."""
    r = get_redis_client()
    groups = load_groups_config()

    for group in groups:
        publish_historical_group(group, r)


# ──────────────────────────────────────────────
# Continuous mode
# ──────────────────────────────────────────────

def watch_all_groups(interval: int = 30):
    """Continuously run all groups with periodic refresh."""
    print(f"\n👁️  Starting Historical Feed Manager (interval={interval}s)...\n")
    while True:
        try:
            run_all_groups()
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Historical feed stopped manually.")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(interval)


# ──────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Historical Feed Manager")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously run in watch mode (default: single run)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Polling interval in seconds (used with --watch)"
    )
    args = parser.parse_args()

    if args.watch:
        watch_all_groups(interval=args.interval)
    else:
        run_all_groups()