"""
producer.py — Market data producer for ELK pipeline.

Generates realistic FX and equity market data events
and indexes them into Elasticsearch.

In production at SocGen:
- Real market feeds (Bloomberg, Reuters) replace simulation
- Logstash ingests and transforms data
- Kibana dashboards monitor market activity
- Alerts fire on anomalies (price spikes, latency, volume)

Usage:
    python producer.py          # continuous mode
    python producer.py --once   # single batch (for testing)
"""

import sys
import time
import random
import logging
from datetime import datetime, timezone
from elasticsearch import Elasticsearch

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s"
)
log = logging.getLogger("producer")

# ── Config ────────────────────────────────────────────────────────
ES_HOST = "http://localhost:9200"
INDEX_NAME = "market-data"
BATCH_SIZE = 10
INTERVAL_SECONDS = 5

# Market instruments
INSTRUMENTS = [
    {"symbol": "EUR/USD", "asset_class": "FX",     "base_price": 1.0823},
    {"symbol": "GBP/USD", "asset_class": "FX",     "base_price": 1.2650},
    {"symbol": "USD/JPY", "asset_class": "FX",     "base_price": 153.40},
    {"symbol": "AAPL",    "asset_class": "EQUITY", "base_price": 185.50},
    {"symbol": "SPX",     "asset_class": "INDEX",  "base_price": 5200.00},
]

# Anomaly simulation — occasional price spikes
ANOMALY_PROBABILITY = 0.05  # 5% chance per event


def create_es_client():
    """Connect to Elasticsearch."""
    client = Elasticsearch(ES_HOST)
    if client.ping():
        log.info("Connected to Elasticsearch at %s", ES_HOST)
        return client
    raise ConnectionError(f"Cannot connect to Elasticsearch at {ES_HOST}")


def create_index(client):
    """
    Create index with proper mapping.
    In production: index templates define mappings for all indices.
    """
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(
            index=INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "timestamp":   {"type": "date"},
                        "symbol":      {"type": "keyword"},
                        "asset_class": {"type": "keyword"},
                        "price":       {"type": "float"},
                        "volume":      {"type": "long"},
                        "bid":         {"type": "float"},
                        "ask":         {"type": "float"},
                        "spread":      {"type": "float"},
                        "latency_ms":  {"type": "integer"},
                        "anomaly":     {"type": "boolean"},
                        "alert_type":  {"type": "keyword"},
                    }
                }
            }
        )
        log.info("Index created: %s", INDEX_NAME)
    else:
        log.info("Index already exists: %s", INDEX_NAME)


def generate_market_event(instrument):
    """
    Generate a realistic market data event.

    Simulates:
    - Price movement with random walk
    - Bid/ask spread
    - Trading volume
    - Execution latency
    - Occasional anomalies (price spikes)
    """
    base_price = instrument["base_price"]

    # Random price movement ±0.5%
    price_change = random.uniform(-0.005, 0.005)
    price = round(base_price * (1 + price_change), 4)

    # Bid/ask spread
    spread = round(random.uniform(0.0001, 0.0005), 4)
    bid = round(price - spread / 2, 4)
    ask = round(price + spread / 2, 4)

    # Volume
    volume = random.randint(100000, 5000000)

    # Latency
    latency_ms = random.randint(10, 200)

    # Anomaly detection
    anomaly = random.random() < ANOMALY_PROBABILITY
    alert_type = None

    if anomaly:
        # Simulate price spike
        price = round(price * random.uniform(1.01, 1.03), 4)
        alert_type = "PRICE_SPIKE"
        log.warning("⚠️  Anomaly detected: %s price spike → %s",
                    instrument["symbol"], price)

    # High latency anomaly
    if latency_ms > 150:
        alert_type = alert_type or "HIGH_LATENCY"

    return {
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "symbol":      instrument["symbol"],
        "asset_class": instrument["asset_class"],
        "price":       price,
        "bid":         bid,
        "ask":         ask,
        "spread":      spread,
        "volume":      volume,
        "latency_ms":  latency_ms,
        "anomaly":     anomaly,
        "alert_type":  alert_type,
    }


def index_batch(client, events):
    """Index a batch of market events into Elasticsearch."""
    for event in events:
        client.index(index=INDEX_NAME, body=event)
    log.info("Indexed %d events → %s", len(events), INDEX_NAME)


def run(once=False):
    """Main loop — generate and index market data."""
    client = create_es_client()
    create_index(client)

    log.info("Starting market data producer — %d instruments",
             len(INSTRUMENTS))

    cycle = 0
    while True:
        cycle += 1
        events = []

        for instrument in INSTRUMENTS:
            event = generate_market_event(instrument)
            events.append(event)

            log.info("[%s] %s → price: %s | latency: %sms%s",
                     event["asset_class"],
                     event["symbol"],
                     event["price"],
                     event["latency_ms"],
                     " ⚠️ ANOMALY" if event["anomaly"] else "")

        index_batch(client, events)
        log.info("Cycle %d complete — %d events indexed\n", cycle, len(events))

        if once:
            break

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    once = "--once" in sys.argv
    run(once=once)