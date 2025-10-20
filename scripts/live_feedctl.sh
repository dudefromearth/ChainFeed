#!/usr/bin/env bash
# 🟢 Live Feed Control — wrapper for feedctl_common.sh

# Always resolve relative to this script's directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${BASE_DIR}/feedctl_common.sh"

MODE="live"

# Start the interactive menu using the shared logic
show_menu "$MODE"