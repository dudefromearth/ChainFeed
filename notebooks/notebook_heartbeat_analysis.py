"""
notebooks/notebook_heartbeat_analysis.py
──────────────────────────────────────────────
Analyze ChainFeed heartbeat telemetry logs.

Features:
  • Uptime ratio per group
  • Average silence duration and recovery count
  • Mean heartbeat latency
  • Timeline visualization (optional)
──────────────────────────────────────────────
"""

import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "heartbeat_history.csv")


def load_heartbeat_log():
    if not os.path.exists(LOG_FILE):
        raise FileNotFoundError(f"❌ No heartbeat log found at {LOG_FILE}")
    df = pd.read_csv(LOG_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df.sort_values(["group", "timestamp"], inplace=True)
    return df


def compute_metrics(df):
    summary = []

    for group, g in df.groupby("group"):
        total_entries = len(g)
        active_time = len(g[g["state"].str.contains("active")])
        silent_time = len(g[g["state"].str.contains("silent")])
        overdue_time = len(g[g["state"].str.contains("overdue")])
        uptime_ratio = active_time / total_entries if total_entries else 0

        # Detect silence segments
        silent_transitions = g[g["state"].str.contains("silent")]["timestamp"]
        recoveries = g[g["state"].str.contains("active")]["timestamp"]

        avg_latency = g["delta_since_last_s"].astype(float).mean()
        total_duration = (g["timestamp"].max() - g["timestamp"].min()).total_seconds()

        summary.append({
            "Group": group,
            "Entries": total_entries,
            "Uptime_Ratio_%": round(uptime_ratio * 100, 2),
            "Mean_Latency_s": round(avg_latency, 2),
            "Silence_Events": len(silent_transitions),
            "Recoveries": len(recoveries),
            "Total_Observed_Min": round(total_duration / 60, 1)
        })

    return pd.DataFrame(summary)


def plot_timeline(df, group):
    """Visualize heartbeat state transitions over time."""
    g = df[df["group"] == group].copy()

    # Ensure proper dtype conversions and alignment
    g = g.reset_index(drop=True)
    g["timestamp"] = pd.to_datetime(g["timestamp"], utc=True, errors="coerce")

    # Map states to colors safely
    color_map = {
        "✅ active": "green",
        "⚠️ overdue": "orange",
        "🚨 silent": "red",
        "❌ never seen": "gray"
    }
    g["color"] = g["state"].map(color_map).fillna("gray")

    # Guard against empty or malformed data
    if g.empty or g["timestamp"].isna().all():
        print(f"⚠️ No valid data to plot for {group}")
        return

    # Ensure matching array lengths for scatter
    x = g["timestamp"].to_list()
    y = [1.0] * len(x)
    colors = g["color"].to_list()

    plt.figure(figsize=(12, 2))
    plt.scatter(x, y, c=colors, s=60, alpha=0.8, edgecolors="none")
    plt.title(f"Heartbeat Timeline — {group}")
    plt.yticks([])
    plt.xlabel("Time (UTC)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.show()

def main():
    df = load_heartbeat_log()
    print(f"✅ Loaded {len(df)} entries from {LOG_FILE}\n")

    summary = compute_metrics(df)
    print("📊 Heartbeat Summary:")
    print(summary.to_string(index=False))

    print("\n──────────────────────────────────────────────")
    groups = summary["Group"].tolist()
    print(f"Groups found: {', '.join(groups)}")

    # Optional visualization per group
    ans = input("\nShow timeline plot for each group? (y/n): ").strip().lower()
    if ans == "y":
        for group in groups:
            plot_timeline(df, group)


if __name__ == "__main__":
    main()