#!/usr/bin/env bash
# ===============================================================
# 🧭 ChainFeed RSS Feed Health Dashboard (with totals)
# ===============================================================

REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}

echo ""
echo "=============================================================="
echo "🧭 ChainFeed RSS Feed Health Dashboard"
echo "=============================================================="
echo ""
echo "Redis Host: ${REDIS_HOST}:${REDIS_PORT}"
echo ""

metrics_keys=$(redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" KEYS "truth:feed:rss:metrics:*" | sed '/^$/d')

if [ -z "$metrics_keys" ]; then
  echo "❌ No RSS metric keys found in Redis."
  echo "Make sure your RSSFeedIngestor is running and publishing metrics."
  exit 0
fi

printf "\n%-35s %-10s %-10s %-10s %-10s %-25s\n" \
"Feed Group" "Status" "Items" "Errors" "Sources" "Last Poll"
printf "%-35s %-10s %-10s %-10s %-10s %-25s\n" \
"-----------" "--------" "------" "------" "--------" "----------"

total_items=0
total_errors=0
total_sources=0

while IFS= read -r key; do
  json=$(redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" GET "$key" 2>/dev/null)

  if [ -n "$json" ] && echo "$json" | jq empty 2>/dev/null; then
    group=$(echo "$json" | jq -r '.group // "unknown"')
    status=$(echo "$json" | jq -r '.status // "unknown"')
    items=$(echo "$json" | jq -r '.new_items // 0')
    errors=$(echo "$json" | jq -r '.errors // 0')
    sources=$(echo "$json" | jq -r '.sources_checked // 0')
    last_poll=$(echo "$json" | jq -r '.last_poll // "n/a"')

    printf "%-35s %-10s %-10s %-10s %-10s %-25s\n" \
      "$group" "$status" "$items" "$errors" "$sources" "$last_poll"

    # accumulate totals
    total_items=$((total_items + items))
    total_errors=$((total_errors + errors))
    total_sources=$((total_sources + sources))
  else
    echo "⚠️  Skipped invalid or empty JSON for key: $key"
  fi
done <<< "$metrics_keys"

# Totals row
printf "%-35s %-10s %-10s %-10s %-10s %-25s\n" \
"TOTAL" "-" "$total_items" "$total_errors" "$total_sources" "-"

echo ""
echo "--------------------------------------------------------------"
echo "📊 Legend: ok = healthy | degraded = partial failure | unknown = offline"
echo "🕓 Run this command periodically or add to your monitoring cron."
echo "--------------------------------------------------------------"