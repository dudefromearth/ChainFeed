#!/usr/bin/env python3
"""
feedctl_logger.py
───────────────────────────────────────────────
Broker-grade Control Plane Logger for ChainFeed
Logs operational events (start, stop, crash, restart)
to Redis in structured JSON for audit, monitoring, and
integration with SSE dashboards.

Now includes dual time awareness:
- UTC timestamp (canonical)
- Local timestamp + timezone info (diagnostic)
"""

import argparse
import json
import os
import socket
import sys
from datetime import datetime, timezone
import redis

try:
    import pytz
except ImportError:
    pytz = None


# ─────────────────────────────────────────────────────────────
# ⚙️  Redis Configuration
# ─────────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_KEY = "control:events"
EVENT_TTL_SEC = 48 * 3600  # 48 hours
MAX_EVENTS = 5000           # optional trim cap


# ─────────────────────────────────────────────────────────────
# 🧩 Redis Connection Helper
# ─────────────────────────────────────────────────────────────
def get_redis_connection():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
# 🕰️  Dual Time Context
# ─────────────────────────────────────────────────────────────
def get_time_context():
    """Return UTC and local timestamps with zone info."""
    utc_now = datetime.now(timezone.utc)
    utc_iso = utc_now.isoformat()
    epoch_ms = int(utc_now.timestamp() * 1000)

    # Derive local time and timezone if pytz or built-in support available
    local_now = utc_now.astimezone()
    local_iso = local_now.isoformat()
    local_tz = str(local_now.tzinfo)

    return {
        "timestamp": utc_iso,
        "epoch_ms": epoch_ms,
        "local_timestamp": local_iso,
        "local_tz": local_tz,
    }


# ─────────────────────────────────────────────────────────────
# 🪶 Event Object Builder
# ─────────────────────────────────────────────────────────────
def build_event(event_type, group, mode, status="ok", reason=None, extra=None):
    """Constructs a structured event JSON for control-plane logging."""
    tctx = get_time_context()
    event = {
        "event": event_type,
        "timestamp": tctx["timestamp"],          # UTC
        "epoch_ms": tctx["epoch_ms"],
        "local_timestamp": tctx["local_timestamp"],
        "local_tz": tctx["local_tz"],
        "group": group,
        "mode": mode,
        "status": status,
        "reason": reason or "manual",
        "user": os.getenv("USER", "unknown"),
        "source_host": socket.gethostname(),
    }
    if extra and isinstance(extra, dict):
        event.update(extra)
    return event


# ─────────────────────────────────────────────────────────────
# 💾 Logging Function
# ─────────────────────────────────────────────────────────────
def log_event(event):
    """Pushes event JSON to Redis (sorted set)."""
    try:
        r = get_redis_connection()
        payload = json.dumps(event)
        r.zadd(REDIS_KEY, {payload: event["epoch_ms"]})
        r.zremrangebyrank(REDIS_KEY, 0, -MAX_EVENTS - 1)
        r.expire(REDIS_KEY, EVENT_TTL_SEC)
        print(f"✅ Logged event: {event['event']} [{event['group']} | {event['mode']}] at {event['timestamp']} UTC")
    except Exception as e:
        print(f"❌ Failed to log event: {e}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────
# 🧰 CLI Interface
# ─────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="ChainFeed Control Logger")
    parser.add_argument("--event", required=True, help="Event type (feed_start, feed_stop, feed_restart, feed_crash)")
    parser.add_argument("--group", required=True, help="Feed group (e.g., spx_complex, ndx_complex)")
    parser.add_argument("--mode", required=True, help="Feed mode (live, historical)")
    parser.add_argument("--status", default="ok", help="Status (ok, error, warning)")
    parser.add_argument("--reason", default=None, help="Reason for event")
    parser.add_argument("--extra", default=None, help="Optional extra JSON payload")
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────
# 🚀 Main
# ─────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    extra = None
    if args.extra:
        try:
            extra = json.loads(args.extra)
        except json.JSONDecodeError:
            print("⚠️  Ignoring invalid --extra JSON payload.", file=sys.stderr)

    event = build_event(
        event_type=args.event,
        group=args.group,
        mode=args.mode,
        status=args.status,
        reason=args.reason,
        extra=extra,
    )
    log_event(event)


if __name__ == "__main__":
    main()