#!/usr/bin/env python3
# ===============================================================
# 🌿 MarketStateValidator — Market Hours & Expiration Awareness
# ===============================================================
# Author:  StudioTwo Build Lab / Convexity GPT
# Date:    2025-10-26
#
# Purpose:
# --------
# Provides time-aware validation logic to determine whether a
# given symbol’s feed should be active or paused.
#
# Handles:
#   • Market hours (weekday / weekend)
#   • Session times (regular vs pre/post-market)
#   • Expiration proximity for weekly options
#
# Returns:
#   (is_valid, reason) tuples for caller logic
#
# ===============================================================

import pytz
from datetime import datetime, time, timedelta


class MarketStateValidator:
    def __init__(self, redis_client=None, logger=None, tz="US/Eastern"):
        self.redis = redis_client
        self.logger = logger
        self.tz = pytz.timezone(tz)

    # -----------------------------------------------------------
    def validate_feed_availability(self, symbol: str):
        """
        Determine if the market is open and the feed should be active.
        Returns: (bool, reason)
        """
        now_utc = datetime.now()
        now_local = now_utc.astimezone(self.tz)

        weekday = now_local.weekday()  # Monday = 0, Sunday = 6
        current_time = now_local.time()

        # --- Weekend check ---
        if weekday >= 5:
            next_open = self._next_open_date(now_local)
            return (
                False,
                f"Market closed for weekend — next open {next_open.strftime('%A %H:%M %Z')}.",
            )

        # --- Regular market session (09:30–16:00 ET) ---
        open_time = time(9, 30)
        close_time = time(16, 0)

        if current_time < open_time:
            return (
                False,
                f"Pre-market hours — opens at {open_time.strftime('%H:%M')} ET.",
            )
        elif current_time > close_time:
            return (
                False,
                f"Post-market hours — closed since {close_time.strftime('%H:%M')} ET.",
            )

        # --- Expiration awareness (for weekly options symbols) ---
        if self._is_weekly_options_symbol(symbol) and weekday == 4 and current_time > time(16, 0):
            return (
                False,
                "Weekly options expired — waiting for next cycle.",
            )

        # --- Passed all checks ---
        return True, "Market open and valid for live feed."

    # -----------------------------------------------------------
    def _is_weekly_options_symbol(self, symbol: str) -> bool:
        """Simple heuristic for weekly options identification."""
        weekly_symbols = {"SPX", "SPY", "ES", "NDX", "QQQ", "NQ"}
        return symbol.upper() in weekly_symbols

    # -----------------------------------------------------------
    def _next_open_date(self, now_local):
        """Find next Monday 09:30 ET."""
        days_ahead = 7 - now_local.weekday()
        next_open = (now_local + timedelta(days=days_ahead)).replace(
            hour=9, minute=30, second=0, microsecond=0
        )
        return next_open