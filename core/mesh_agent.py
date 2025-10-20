#!/usr/bin/env python3
"""
Redis Mesh Agent — v1.0
--------------------------------
Each node (Developer or Production) runs a MeshAgent process.
It forms a federated mesh across all nodes using Redis Pub/Sub.
"""

import json
import os
import time
import socket
import threading
import redis
from datetime import datetime, timezone

# ======================================================
# Configuration
# ======================================================

NODE_NAME = os.getenv("NODE_NAME", socket.gethostname())
NODE_ROLE = os.getenv("NODE_ROLE", "production")  # "developer" or "production"
NODE_GROUPS = os.getenv("NODE_GROUPS", "spx_complex").split(",")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 10))  # seconds
MESH_CHANNEL_PREFIX = os.getenv("MESH_CHANNEL_PREFIX", "mesh")

# ======================================================
# Connect to Redis
# ======================================================

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    print(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"❌ Failed to connect to Redis: {e}")
    exit(1)

# ======================================================
# Local Node Registry
# ======================================================

def update_local_registry(node_id, info):
    """Store node info in local Redis registry."""
    key = f"{MESH_CHANNEL_PREFIX}:nodes"
    r.hset(key, node_id, json.dumps(info))
    r.expire(key, 300)  # auto-expire if no update for 5 min

def get_all_nodes():
    """Return all known nodes from local registry."""
    key = f"{MESH_CHANNEL_PREFIX}:nodes"
    data = r.hgetall(key)
    return {k: json.loads(v) for k, v in data.items()}

# ======================================================
# Heartbeat Publisher
# ======================================================

def publish_heartbeat():
    """Periodically broadcast node health and metadata."""
    while True:
        payload = {
            "node": NODE_NAME,
            "role": NODE_ROLE,
            "groups": NODE_GROUPS,
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        channel = f"{MESH_CHANNEL_PREFIX}:heartbeat"
        r.publish(channel, json.dumps(payload))
        update_local_registry(NODE_NAME, payload)
        time.sleep(HEARTBEAT_INTERVAL)

# ======================================================
# Mesh Listener
# ======================================================

def listen_for_mesh_messages():
    """Listen for mesh messages: heartbeats, syncs, commands."""
    pubsub = r.pubsub()
    channels = [
        f"{MESH_CHANNEL_PREFIX}:heartbeat",
        f"{MESH_CHANNEL_PREFIX}:commands",
        f"{MESH_CHANNEL_PREFIX}:sync"
    ]
    pubsub.subscribe(channels)

    print(f"🛰️  Listening for mesh messages on {channels}")

    for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        channel = msg["channel"]
        try:
            payload = json.loads(msg["data"])
        except Exception:
            continue

        # Handle heartbeats
        if channel.endswith("heartbeat"):
            if payload["node"] != NODE_NAME:
                update_local_registry(payload["node"], payload)

        # Handle commands (developer node can send these)
        elif channel.endswith("commands"):
            handle_command(payload)

        # Handle config sync
        elif channel.endswith("sync"):
            handle_sync(payload)

# ======================================================
# Command Handlers
# ======================================================

def handle_command(cmd):
    """Execute incoming mesh command."""
    action = cmd.get("cmd")
    target = cmd.get("target")
    print(f"⚙️  Received command: {cmd}")

    # Only act if target matches this node or "all"
    if target not in [NODE_NAME, "all"]:
        return

    if action == "restart_feed":
        os.system("pkill -f live_feed_manager.py && python -m core.live_feed_manager &")
    elif action == "sync_config":
        os.system("python -m config.sync_config")
    elif action == "heartbeat_ping":
        r.publish(f"{MESH_CHANNEL_PREFIX}:ack", json.dumps({
            "node": NODE_NAME,
            "ack": "pong",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))

def handle_sync(payload):
    """Apply configuration sync from developer node."""
    print(f"🔄 Received config sync: {payload.get('source')} → updating local groups.yaml")

# ======================================================
# Main Entry
# ======================================================

def main():
    print(f"🚀 Starting Redis Mesh Agent for node: {NODE_NAME}")
    threading.Thread(target=publish_heartbeat, daemon=True).start()
    listen_for_mesh_messages()

if __name__ == "__main__":
    main()