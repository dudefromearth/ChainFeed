#!/usr/bin/env bash
# ===============================================================
# 📰 ChainFeed — Show latest RSS headlines (across all groups)
# ===============================================================
# Prints the N most recent items found under truth:feed:rss:* (excluding metrics/registry).
#
# Usage:
#   ./scripts/show_rss_headlines.sh [N]
#   N defaults to 10
# ===============================================================

set -euo pipefail

REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
LIMIT=${1:-10}

echo ""
echo "=============================================================="
echo "📰 ChainFeed — Latest RSS Headlines (top ${LIMIT})"
echo "=============================================================="
echo "Redis Host: ${REDIS_HOST}:${REDIS_PORT}"
echo ""

# Collect item keys (exclude metrics + registry)
mapfile -t ITEM_KEYS < <(redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" \
  KEYS "truth:feed:rss:*" | grep -v -E 'metrics|registry')

if [ ${#ITEM_KEYS[@]} -eq 0 ]; then
  echo "❌ No RSS items found. Is the RSSFeedIngestor running?"
  exit 0
fi

# Pull all items -> newline-delimited JSON
ITEMS_JSON=""
for k in "${ITEM_KEYS[@]}"; do
  val=$(redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" GET "$k")
  if [ -n "$val" ] && echo "$val" | jq empty >/dev/null 2>&1; then
    echo "$val"
  fi
done | jq -c '.' > /tmp/rss_items.jsonl

if [ ! -s /tmp/rss_items.jsonl ]; then
  echo "❌ RSS item values are empty or invalid JSON."
  exit 0
fi

# Sort by published timestamp desc (fall back to timestamp if published missing), then show top N
echo "Top ${LIMIT} items:"
echo "--------------------------------------------------------------------------------"
jq -s \
  'map(. + {__sort_ts: ( .published // .timestamp // "" )})
   | sort_by(.__sort_ts)
   | reverse
   | .[:'"${LIMIT}"']
   | .[]
   | {
       group: (.group // "unknown"),
       source: (.source // .feed // "unknown"),
       title: (.title // "untitled"),
       published: (.published // .timestamp // "n/a"),
       url: (.url // .link // "n/a")
     }' /tmp/rss_items.jsonl \
| jq -r '
  [.group, .source, .published, .title, .url]
  | @tsv' \
| while IFS=$'\t' read -r group source published title url; do
    printf "• [%s] (%s)\n  %s\n  %s\n\n" "$group" "$published" "$title" "$url"
  done

echo "--------------------------------------------------------------------------------"
