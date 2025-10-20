#!/usr/bin/env bash
# 🟣 Historical Feed Control — wrapper for feedctl_common.sh

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${BASE_DIR}/feedctl_common.sh"

MODE="historical"

show_menu "$MODE"