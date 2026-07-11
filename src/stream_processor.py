"""
stream_processor.py — Real-Time Price Monitoring & Alert Simulation

Simulates a streaming data pipeline that monitors Airbnb listing prices in
near-real-time. Generates synthetic price update events, detects anomalies
(prices deviating > 2 std deviations from their neighbourhood median), and
emits structured alert records to a JSON log file.

Architecture Context:
    In production this would run with Apache Kafka / AWS Kinesis as the
    event backbone. This simulation uses an in-process queue and threading
    to demonstrate the same logic patterns without cloud infrastructure.

Usage:
    python src/stream_processor.py [--duration 30] [--rate 0.5]

    --duration : seconds to run the simulation (default 30)
    --rate     : events per second to generate (default 2)
"""

import pandas as pd
import numpy as np
import json
import time
import threading
import queue
import argparse
import os
import sys
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
ENRICHED_LISTINGS_PATH = "data/processed/enriched_listings.csv"
ALERT_OUTPUT_PATH      = "reports/stream_alerts.json"
EVENT_OUTPUT_PATH      = "reports/stream_events.json"

# Anomaly detection thresholds
PRICE_ANOMALY_STD_MULTIPLIER = 2.0   # >2 std devs from neighbourhood median
EXTREME_PRICE_FLOOR          = 10    # $10 minimum (data quality)
EXTREME_PRICE_CEILING        = 5000  # $5,000 maximum (data quality)

# Simulation parameters
DEFAULT_DURATION_SECONDS = 30
DEFAULT_EVENTS_PER_SECOND = 2.0
MAX_EVENTS_LOG             = 200  # cap log file size


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING & BASELINE STATISTICS
# ─────────────────────────────────────────────────────────────────────────────
def load_baseline_stats(path: str) -> dict:
    """
    Load enriched listings and compute per-neighbourhood price statistics.
    Returns a dict keyed by neighbourhood_group_cleansed.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Enriched listings not found at '{path}'. "
            "Run 'python src/pipeline.py' first."
        )
    df = pd.read_csv(path)
    required_cols = {"neighbourhood_group_cleansed", "price", "id"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")

    # Remove extreme values for baseline calculation
    df = df[df["price"].between(EXTREME_PRICE_FLOOR, EXTREME_PRICE_CEILING)]

    stats = {}
    for borough, group in df.groupby("neighbourhood_group_cleansed"):
        median  = group["price"].median()
        std     = group["price"].std()
        mean    = group["price"].mean()
        min_p   = group["price"].quantile(0.05)
        max_p   = group["price"].quantile(0.95)
        stats[borough] = {
            "median": round(median, 2),
            "std":    round(std, 2),
            "mean":   round(mean, 2),
            "p05":    round(min_p, 2),
            "p95":    round(max_p, 2),
            "count":  len(group),
            "sample_listing_ids": group["id"].sample(min(50, len(group))).tolist(),
        }
    return stats, df


# ─────────────────────────────────────────────────────────────────────────────
# EVENT GENERATOR (Producer Thread)
# ─────────────────────────────────────────────────────────────────────────────
class PriceEventGenerator(threading.Thread):
    """
    Simulates a Kafka/Kinesis producer publishing listing price update events.
    Each event represents a host updating their nightly price.
    """

    def __init__(self, baseline_stats: dict, df: pd.DataFrame,
                 event_queue: queue.Queue, events_per_second: float,
                 duration: float, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.stats          = baseline_stats
        self.df             = df
        self.queue          = event_queue
        self.rate           = events_per_second
        self.duration       = duration
        self.stop_event     = stop_event
        self.boroughs       = list(baseline_stats.keys())
        self.events_emitted = 0

    def _generate_event(self) -> dict:
        """Generate a single synthetic price update event."""
        borough = np.random.choice(self.boroughs)
        borough_stats = self.stats[borough]
        listing_id = np.random.choice(borough_stats["sample_listing_ids"])

        # 85% normal price variation; 15% anomalous price (spike or drop)
        if np.random.random() < 0.85:
            # Normal: price within ±1.5 std devs of median
            noise = np.random.normal(0, borough_stats["std"] * 0.5)
            price = max(EXTREME_PRICE_FLOOR,
                        borough_stats["median"] + noise)
        else:
            # Anomalous: price jump/drop of 2.5–4× std dev
            direction = 1 if np.random.random() > 0.4 else -1
            multiplier = np.random.uniform(2.5, 4.0)
            price = max(EXTREME_PRICE_FLOOR,
                        borough_stats["median"] + direction * multiplier * borough_stats["std"])

        # Clip to realistic bounds
        price = round(min(price, EXTREME_PRICE_CEILING), 2)

        return {
            "event_id":   f"evt_{int(time.time() * 1000)}_{np.random.randint(1000, 9999)}",
            "listing_id": int(listing_id),
            "borough":    borough,
            "price":      price,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "event_type": "PRICE_UPDATE",
        }

    def run(self):
        start = time.monotonic()
        interval = 1.0 / self.rate
        while not self.stop_event.is_set():
            elapsed = time.monotonic() - start
            if elapsed >= self.duration:
                self.stop_event.set()
                break
            event = self._generate_event()
            self.queue.put(event)
            self.events_emitted += 1
            time.sleep(interval)


# ─────────────────────────────────────────────────────────────────────────────
# ANOMALY DETECTOR & ALERTER (Consumer Thread)
# ─────────────────────────────────────────────────────────────────────────────
class PriceAnomalyDetector(threading.Thread):
    """
    Simulates a Flink/Kinesis Analytics consumer that reads price events and
    emits alerts when prices deviate significantly from neighbourhood baselines.
    """

    def __init__(self, baseline_stats: dict, event_queue: queue.Queue,
                 stop_event: threading.Event, verbose: bool = True):
        super().__init__(daemon=True)
        self.stats       = baseline_stats
        self.queue       = event_queue
        self.stop_event  = stop_event
        self.verbose     = verbose
        self.alerts      = []
        self.events_seen = []
        self.processed   = 0
        self.anomaly_count = 0

    def _classify_anomaly(self, price: float, borough: str) -> tuple:
        """Returns (is_anomaly, severity, description)."""
        s = self.stats[borough]
        z_score = (price - s["median"]) / max(s["std"], 1.0)  # avoid div/0

        if abs(z_score) < PRICE_ANOMALY_STD_MULTIPLIER:
            return False, None, None
        elif z_score > 0:
            if z_score > 3.5:
                severity = "CRITICAL"
                desc = f"Extreme price spike: ${price:.0f} vs. median ${s['median']:.0f} (z={z_score:.1f})"
            else:
                severity = "WARNING"
                desc = f"Price spike detected: ${price:.0f} vs. median ${s['median']:.0f} (z={z_score:.1f})"
        else:
            if z_score < -3.5:
                severity = "CRITICAL"
                desc = f"Extreme price drop: ${price:.0f} vs. median ${s['median']:.0f} (z={z_score:.1f})"
            else:
                severity = "WARNING"
                desc = f"Unusual price drop: ${price:.0f} vs. median ${s['median']:.0f} (z={z_score:.1f})"

        return True, severity, desc

    def _build_alert(self, event: dict, severity: str, description: str) -> dict:
        s = self.stats[event["borough"]]
        pct_deviation = ((event["price"] - s["median"]) / s["median"]) * 100
        return {
            "alert_id":       f"alrt_{int(time.time() * 1000)}",
            "severity":       severity,
            "description":    description,
            "listing_id":     event["listing_id"],
            "borough":        event["borough"],
            "reported_price": event["price"],
            "neighbourhood_median": s["median"],
            "pct_deviation":  round(pct_deviation, 1),
            "triggered_at":   event["timestamp"],
            "recommended_action": (
                "Flag for manual review and notify host"
                if severity == "CRITICAL"
                else "Log for monitoring and track for 48h"
            ),
        }

    def run(self):
        while not (self.stop_event.is_set() and self.queue.empty()):
            try:
                event = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue

            self.processed += 1
            self.events_seen.append(event)

            is_anomaly, severity, desc = self._classify_anomaly(
                event["price"], event["borough"]
            )
            if is_anomaly:
                alert = self._build_alert(event, severity, desc)
                self.alerts.append(alert)
                self.anomaly_count += 1
                if self.verbose:
                    icon = "🚨" if severity == "CRITICAL" else "⚠️"
                    print(f"{icon}  [{severity}] {desc} — {event['borough']}")

            elif self.verbose and self.processed % 10 == 0:
                print(f"✅  Processed {self.processed} events | "
                      f"{self.anomaly_count} anomalies detected")

            self.queue.task_done()


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def run_simulation(duration: float = DEFAULT_DURATION_SECONDS,
                   events_per_second: float = DEFAULT_EVENTS_PER_SECOND,
                   verbose: bool = True) -> dict:
    """
    Run the full stream processing simulation.

    Returns a summary dict with event counts, alert counts, and file paths.
    """
    print("\n" + "="*60)
    print("  HostLens — Price Stream Monitor Simulation")
    print(f"  Duration: {duration}s | Rate: {events_per_second} events/s")
    print("="*60)

    # Load baseline
    print("\n📊 Loading listing data and computing baseline statistics...")
    baseline_stats, df = load_baseline_stats(ENRICHED_LISTINGS_PATH)
    print(f"   ✓ {len(baseline_stats)} boroughs loaded | "
          f"{sum(v['count'] for v in baseline_stats.values()):,} listings")

    # Print baseline table
    print("\n📈 Neighbourhood Baseline Prices:")
    for borough, s in baseline_stats.items():
        print(f"   {borough:<25} median=${s['median']:.0f}  "
              f"std=${s['std']:.0f}  n={s['count']:,}")

    # Set up threading primitives
    event_queue = queue.Queue(maxsize=1000)
    stop_event  = threading.Event()

    # Spin up producer + consumer
    producer = PriceEventGenerator(
        baseline_stats, df, event_queue,
        events_per_second, duration, stop_event
    )
    consumer = PriceAnomalyDetector(
        baseline_stats, event_queue, stop_event, verbose
    )

    print(f"\n🚀 Starting simulation for {duration} seconds...\n")
    start_time = time.monotonic()

    consumer.start()
    producer.start()
    producer.join()
    consumer.join(timeout=duration + 5)

    elapsed = time.monotonic() - start_time

    # Persist results
    os.makedirs("reports", exist_ok=True)

    alerts_to_save = consumer.alerts
    events_to_save = consumer.events_seen[-MAX_EVENTS_LOG:]  # keep last N

    with open(ALERT_OUTPUT_PATH, "w") as f:
        json.dump({
            "simulation_run": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(elapsed, 1),
            "events_processed": consumer.processed,
            "anomalies_detected": consumer.anomaly_count,
            "anomaly_rate_pct": round(
                (consumer.anomaly_count / max(consumer.processed, 1)) * 100, 1
            ),
            "alerts": alerts_to_save,
        }, f, indent=2)

    with open(EVENT_OUTPUT_PATH, "w") as f:
        json.dump(events_to_save, f, indent=2)

    summary = {
        "duration_s":        round(elapsed, 1),
        "events_emitted":    producer.events_emitted,
        "events_processed":  consumer.processed,
        "anomalies_detected": consumer.anomaly_count,
        "anomaly_rate_pct":  round(
            (consumer.anomaly_count / max(consumer.processed, 1)) * 100, 1
        ),
        "critical_alerts":   sum(1 for a in consumer.alerts if a["severity"] == "CRITICAL"),
        "warning_alerts":    sum(1 for a in consumer.alerts if a["severity"] == "WARNING"),
        "alert_file":        ALERT_OUTPUT_PATH,
        "events_file":       EVENT_OUTPUT_PATH,
        "baseline_stats":    baseline_stats,
        "raw_alerts":        consumer.alerts,
        "raw_events":        events_to_save,
    }

    # Print final summary
    print("\n" + "="*60)
    print("  📊 Simulation Complete — Summary")
    print("="*60)
    print(f"  ⏱️  Duration:          {summary['duration_s']}s")
    print(f"  📨  Events Processed:  {summary['events_processed']:,}")
    print(f"  🚨  Critical Alerts:   {summary['critical_alerts']}")
    print(f"  ⚠️   Warning Alerts:    {summary['warning_alerts']}")
    print(f"  📉  Anomaly Rate:      {summary['anomaly_rate_pct']}%")
    print(f"  💾  Alerts saved to:   {summary['alert_file']}")
    print("="*60 + "\n")

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="HostLens Real-Time Price Monitoring Simulation"
    )
    parser.add_argument(
        "--duration", type=float, default=DEFAULT_DURATION_SECONDS,
        help=f"Simulation duration in seconds (default: {DEFAULT_DURATION_SECONDS})"
    )
    parser.add_argument(
        "--rate", type=float, default=DEFAULT_EVENTS_PER_SECOND,
        help=f"Events per second to simulate (default: {DEFAULT_EVENTS_PER_SECOND})"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress per-event output"
    )
    args = parser.parse_args()

    run_simulation(
        duration=args.duration,
        events_per_second=args.rate,
        verbose=not args.quiet,
    )
