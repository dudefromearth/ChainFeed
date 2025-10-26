#!/usr/bin/env bash
# ===============================================================
# 🌿 ChainFeed — Node Entity Self-Discovery and Status Utility (v2.1)
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# This diagnostic utility identifies and reports the entity assigned
# to *this node*. It reads Redis to:
#   • Discover the node's ID and matching entity.
#   • Display the entity's seat, presence, and contract.
#
# Optional flags:
#   --list-divisions     → List all entities grouped by division
#   --list-organizations → List all entities grouped by organization
#
# Usage:
#   bash ./scripts/check_entity_status.sh
#
# ===============================================================

set -e
set -u

# --- Environment Defaults ---
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}

FLAG_LIST_DIVISIONS=false
FLAG_LIST_ORGS=false

# --- Parse Arguments (for federation options) ---
for arg in "$@"; do
  case $arg in
    --list-divisions)
      FLAG_LIST_DIVISIONS=true
      shift
      ;;
    --list-organizations)
      FLAG_LIST_ORGS=true
      shift
      ;;
    *)
      ;;
  esac
done

# --- Derive Node ID ---
NODE_ID_ENV=${NODE_ID:-}
if [ -z "${NODE_ID_ENV}" ] || [ "${NODE_ID_ENV}" = "hostname" ]; then
  NODE_ID="$(hostname | tr '[:upper:]' '[:lower:]')_chainfeed"
else
  NODE_ID="${NODE_ID_ENV,,}"
fi

# --- Display Header ---
echo "=============================================================="
echo "🌿 ChainFeed Entity Status Report"
echo "Node ID : ${NODE_ID}"
echo "Redis   : ${REDIS_HOST}:${REDIS_PORT}"
echo "=============================================================="

# --- Federation listing options ---
if $FLAG_LIST_DIVISIONS; then
  echo "📋 Listing entities grouped by division..."
  redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" KEYS "truth:node:entity:*" | while read -r key; do
    val=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "$key")
    if command -v jq >/dev/null 2>&1; then
      echo "$val" | jq -r '.division + " → " + .entity_name'
    else
      echo "$val"
    fi
  done | sort
  exit 0
fi

if $FLAG_LIST_ORGS; then
  echo "🏛 Listing entities grouped by organization..."
  redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" KEYS "truth:node:entity:*" | while read -r key; do
    val=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "$key")
    if command -v jq >/dev/null 2>&1; then
      echo "$val" | jq -r '.organization + " → " + .entity_name'
    else
      echo "$val"
    fi
  done | sort
  exit 0
fi

# --- Discover the entity assigned to this node ---
ENTITY_DATA=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "truth:node:entity:${NODE_ID}" 2>/dev/null || true)

if [ -z "$ENTITY_DATA" ]; then
  echo "⚠️  No entity assignment found for node: ${NODE_ID}"
  echo "    Try running with --list-divisions or --list-organizations."
  echo "=============================================================="
  exit 0
fi

# --- Extract core entity fields ---
if command -v jq >/dev/null 2>&1; then
  ENTITY_NAME=$(echo "$ENTITY_DATA" | jq -r '.entity_name')
  ENTITY_DIVISION=$(echo "$ENTITY_DATA" | jq -r '.division')
  ENTITY_ORG=$(echo "$ENTITY_DATA" | jq -r '.organization')
else
  ENTITY_NAME=$(echo "$ENTITY_DATA" | grep -o '"entity_name":"[^"]*' | cut -d'"' -f4)
  ENTITY_DIVISION=$(echo "$ENTITY_DATA" | grep -o '"division":"[^"]*' | cut -d'"' -f4)
  ENTITY_ORG=$(echo "$ENTITY_DATA" | grep -o '"organization":"[^"]*' | cut -d'"' -f4)
fi

ENTITY_KEY=$(echo "$ENTITY_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')

echo "✅ Entity       : ${ENTITY_NAME}"
echo "🏛 Organization : ${ENTITY_ORG}"
echo "🏷  Division    : ${ENTITY_DIVISION}"
echo ""

# --- Define keys ---
STATUS_KEY="truth:convexity:status:${ENTITY_KEY}"
PRESENCE_KEY="truth:convexity:presence:${ENTITY_KEY}"
CONTRACT_KEY="truth:convexity:contract:${ENTITY_KEY}"

# --- Helper for plain string values ---
function show_value() {
  local key="$1"
  local val
  val=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "$key" 2>/dev/null || true)
  if [ -z "$val" ]; then
    echo "⚠️  $key → (nil)"
  else
    echo "✅ $key → $val"
  fi
}

# --- Helper for JSON values ---
function show_json() {
  local key="$1"
  local val
  val=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "$key" 2>/dev/null || true)
  if [ -z "$val" ]; then
    echo "⚠️  $key → (nil)"
  elif command -v jq >/dev/null 2>&1; then
    echo "✅ $key →"
    echo "$val" | jq .
  else
    echo "✅ $key → $val"
  fi
}

# --- Status Readout ---
echo "--------------------------------------------------------------"
echo "📡 Checking Redis keys for ${ENTITY_NAME}..."
echo "--------------------------------------------------------------"

show_value "$STATUS_KEY"
show_value "$PRESENCE_KEY"
show_json "$CONTRACT_KEY"

# --- Summary ---
STATUS=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "$STATUS_KEY" 2>/dev/null || true)
PRESENCE=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "$PRESENCE_KEY" 2>/dev/null || true)

echo ""
echo "--------------------------------------------------------------"
if [ "$STATUS" = "initialized" ] && [ "$PRESENCE" = "active" ]; then
  echo "🌱 Entity ${ENTITY_NAME} is active and seated properly."
elif [ -n "$STATUS" ] && [ -z "$PRESENCE" ]; then
  echo "🪶 Entity seat prepared, but arrival not yet announced."
elif [ -z "$STATUS" ] && [ -z "$PRESENCE" ]; then
  echo "⚠️  No presence or seat found for ${ENTITY_NAME}."
else
  echo "🌀 Entity ${ENTITY_NAME} is in a transitional state."
fi
echo "--------------------------------------------------------------"
echo "Check complete at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=============================================================="