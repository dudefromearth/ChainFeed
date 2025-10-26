#!/usr/bin/env bash
# ===============================================================
# 🌿 FeedChain Proof Runner
# ===============================================================
# Purpose:
#   Shell wrapper to execute the FeedChain proof harness with
#   specified arguments and environment.
#
# Usage:
#   ./scripts/run_feedchain_proof.sh [SYMBOL] [ITERATIONS] [INTERVAL]
#
# Example:
#   ./scripts/run_feedchain_proof.sh ES 2 10
#
# Notes:
#   - Requires Redis and all core ChainFeed components running.
#   - Invokes the full orchestration stack, not mocks.
# ===============================================================

set -e

SYMBOL=${1:-ES}
ITERATIONS=${2:-2}
INTERVAL=${3:-10}

echo "🌿 Starting FeedChain proof harness for $SYMBOL ($ITERATIONS iterations, ${INTERVAL}s interval)..."
echo "---------------------------------------------------------------"

# Execute proof harness (relative to project root)
python3 proofs/feedchain_test_harness.py "$SYMBOL" "$ITERATIONS" "$INTERVAL"

echo "---------------------------------------------------------------"
echo "✅ FeedChain proof harness completed successfully."