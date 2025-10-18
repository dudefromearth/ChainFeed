# core/constants.py

DEFAULT_SYMBOLS = ["SPX", "ES"]
DEFAULT_DTE_RANGE = range(0, 6)  # 0DTE to 5DTE

class FeedMode:
    LIVE = "live"
    BACKFILL = "backfill"
    SYNTHETIC = "synthetic"

class FeedComponent:
    FULL = "FULL"
    DIFF = "DIFF"
    HEARTBEAT = "HEARTBEAT"

ALL_FEEDS = [FeedComponent.FULL, FeedComponent.DIFF, FeedComponent.HEARTBEAT]