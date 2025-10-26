#!/usr/bin/env bash
# ===============================================================
# 🌿 ChainFeed Startup Script (v2.1)
# ===============================================================
# Author: StudioTwo Build Lab / Convexity GPT
# Date:   2025-10-26
#
# Purpose:
# --------
# This script bootstraps the entire ChainFeed runtime stack.
# It ensures that:
#   - The Python virtual environment is active.
#   - Redis is reachable and healthy.
#   - The canonical truth file exists.
#   - The core startup sequence runs cleanly.
#   - Logs are captured both to stdout and to /logs/startup.log.
#
# Now also displays:
#   - Entity identity assigned to this node (from canonical truth)
#
# ===============================================================

set -e  # Exit immediately on error
set -u  # Error on unset variables

# --- Ensure PYTHONPATH is defined to avoid unbound warnings ---
export PYTHONPATH="${PYTHONPATH:-}"

# --- Resolve project paths ---
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/startup_$(date +'%Y%m%d_%H%M%S').log"

VENV_DIR="${ROOT_DIR}/.venv"
PYTHON="${VENV_DIR}/bin/python"

# --- Environment Defaults ---
export REDIS_HOST=${REDIS_HOST:-localhost}
export REDIS_PORT=${REDIS_PORT:-6379}
export CHAINFEED_MODE=${CHAINFEED_MODE:-LIVE}

# --- Node Identity ---
if [ -z "${NODE_ID+x}" ] || [ -z "${NODE_ID}" ] || [ "${NODE_ID}" = "hostname" ]; then
  NODE_ID="$(hostname | tr '[:upper:]' '[:lower:]')_chainfeed"
  export NODE_ID
else
  NODE_ID="$(echo "${NODE_ID}" | tr '[:upper:]' '[:lower:]')"
  export NODE_ID
fi

# --- Check Virtual Environment ---
if [ ! -x "${PYTHON}" ]; then
  echo "❌ Python virtual environment not found at ${PYTHON}"
  echo "   Please run: python3 -m venv .venv && source .venv/bin/activate"
  exit 1
fi

# --- Check Redis Connectivity ---
if ! redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping > /dev/null 2>&1; then
  echo "❌ Redis not reachable at ${REDIS_HOST}:${REDIS_PORT}"
  echo "   Please ensure Redis is running before starting ChainFeed."
  exit 1
else
  echo "✅ Redis reachable at ${REDIS_HOST}:${REDIS_PORT}"
fi

# --- Check Canonical Truth Schema ---
TRUTH_PATH="${ROOT_DIR}/config/canonical_truth.json"
if [ ! -f "${TRUTH_PATH}" ]; then
  echo "❌ Canonical truth schema missing at ${TRUTH_PATH}"
  echo "   Ensure config/canonical_truth.json exists."
  exit 1
fi

# --- Determine Assigned Entity (if any) ---
ENTITY_NAME="Unassigned"
ENTITY_DIVISION=""

# Use jq to safely parse JSON (required)
if command -v jq >/dev/null 2>&1; then
  ENTITY_JSON=$(jq -r --arg NODE_ID "$NODE_ID" \
    '.entities[]? | select(.node_id == $NODE_ID)' "${TRUTH_PATH}" 2>/dev/null || true)

  if [ -n "${ENTITY_JSON}" ]; then
    ENTITY_NAME=$(echo "${ENTITY_JSON}" | jq -r '.name')
    ENTITY_DIVISION=$(echo "${ENTITY_JSON}" | jq -r '.division')
  fi
else
  echo "⚠️ jq not installed — cannot resolve entity identity from truth."
fi

# --- Display Startup Banner ---
echo "=============================================================="
echo "🌿 Starting ChainFeed v2.0 — Mode: ${CHAINFEED_MODE}"
if [ "${ENTITY_NAME}" != "Unassigned" ]; then
  echo "Entity       : ${ENTITY_NAME} (${ENTITY_DIVISION} Division)"
else
  echo "Entity       : Unassigned (no matching entity in truth)"
fi
echo "Node ID      : ${NODE_ID}"
echo "Project Root : ${ROOT_DIR}"
echo "Log File     : ${LOG_FILE}"
echo "Redis        : ${REDIS_HOST}:${REDIS_PORT}"
echo "=============================================================="
echo ""

# --- Activate Virtual Environment ---
source "${VENV_DIR}/bin/activate"

# --- Launch Startup Sequence ---
echo ""
echo "🚀 Launching ChainFeed startup sequence..."
echo ""

"${PYTHON}" -m core.startup.startup_sequence 2>&1 | tee -a "${LOG_FILE}"

# --- Post-Run Status ---
EXIT_CODE=${PIPESTATUS[0]}
if [ ${EXIT_CODE} -eq 0 ]; then
  echo ""
  echo "🌳 ChainFeed startup sequence completed successfully."
  echo "Log saved to: ${LOG_FILE}"
else
  echo ""
  echo "❌ ChainFeed startup failed with exit code ${EXIT_CODE}."
  echo "Check logs for details: ${LOG_FILE}"
  exit ${EXIT_CODE}
fi

echo "=============================================================="
echo "🌀 System is live. Runtime loop should now be active."
echo "Monitor status via Redis key: truth:system:startup_status"
echo "=============================================================="