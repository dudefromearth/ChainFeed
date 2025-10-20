"""
core/live_feed_manager.py
Simulated Live Feed Manager
---------------------------------
Temporary live mode simulator until live Polygon integration.
"""

import time
import sys
from datetime import datetime, timezone

def main():
    group = None
    if "--group" in sys.argv:
        idx = sys.argv.index("--group")
        if idx + 1 < len(sys.argv):
            group = sys.argv[idx + 1]

    group = group or "spx_complex"
    print(f"🚀 Starting simulated Live Feed for group: {group}")
    print("🧩 Publishing fake data every 5 seconds (Ctrl+C to stop)")

    try:
        while True:
            timestamp = datetime.now(timezone.utc).isoformat()
            print(f"[{timestamp}] 🔄 Live tick for {group}")
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n🛑 Live feed for {group} stopped manually at {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    main()