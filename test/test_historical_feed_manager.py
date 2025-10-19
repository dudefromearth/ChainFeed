"""
test/test_historical_feed_manager.py
──────────────────────────────────────────────
Integration test for historical_feed_manager using a live Redis instance.

This test:
- Connects to local Redis
- Loads group definitions from groups.yaml
- Runs the historical ingestion + publishing cycle
- Validates Redis key creation, structure, and data types
- Confirms UTC-aware timestamps in both snapshot and heartbeat
──────────────────────────────────────────────
"""

import os
import json
import redis
from datetime import datetime, timezone

from core.historical_feed_manager import (
    load_groups_config,
    publish_historical_group,
    update_heartbeat,
    get_redis_client,
)


def decode_redis_value(raw):
    """Safely decode bytes → UTF-8 string."""
    if raw is None:
        return None
    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    return raw


def test_historical_feed_manager_end_to_end():
    """Full integration test using local Redis instance."""
    print("\n🔍 Starting historical feed manager integration test...\n")

    # 1️⃣ Connect to Redis
    r = get_redis_client()

    # 2️⃣ Load groups.yaml
    groups = load_groups_config("groups.yaml")
    assert groups, "⚠️ No groups found in groups.yaml"
    group = groups[0]
    group_key = group["key"]

    print(f"🧠 Testing group: {group_key} ({group['name']})")

    # 3️⃣ Run full publishing cycle
    publish_historical_group(group, r)

    # 4️⃣ Validate each member snapshot in Redis
    for member in group["members"]:
        symbol = member["symbol"]
        redis_key = f"chain:{group_key}:{symbol}:snapshot"

        raw_data = r.get(redis_key)
        assert raw_data is not None, f"❌ Missing Redis key for {symbol}"

        data = decode_redis_value(raw_data)
        parsed = json.loads(data)

        # Structural checks
        assert isinstance(parsed, dict), f"❌ {symbol} data not dict type"
        assert "contracts" in parsed, f"❌ {symbol} missing 'contracts'"
        assert isinstance(parsed["contracts"], list), f"❌ {symbol} 'contracts' not list type"
        assert "published_at" in parsed, f"❌ {symbol} missing 'published_at' timestamp"

        # Timestamp integrity check
        ts = datetime.fromisoformat(parsed["published_at"])
        assert ts.tzinfo == timezone.utc, f"❌ {symbol} timestamp not UTC-aware"

        print(f"✅ Verified {redis_key} (contracts={len(parsed['contracts'])})")

    # 5️⃣ Update and validate heartbeat
    update_heartbeat(group, r)

    hb_key = f"heartbeat:{group_key}"
    raw_hb = r.get(hb_key)
    assert raw_hb, "❌ Heartbeat key not found"
    hb = json.loads(decode_redis_value(raw_hb))

    assert hb["status"] == "alive", "❌ Heartbeat status incorrect"
    ts = datetime.fromisoformat(hb["timestamp"])
    assert ts.tzinfo == timezone.utc, "❌ Heartbeat timestamp not UTC-aware"
    assert set(hb["symbols"]) == {m["symbol"] for m in group["members"]}, "❌ Heartbeat symbols mismatch"

    print(f"💓 Heartbeat OK for {group_key} ({hb['timestamp']})")

    print("\n🏁 Historical feed manager end-to-end test passed successfully.\n")


if __name__ == "__main__":
    import pytest
    pytest.main([os.path.abspath(__file__)])