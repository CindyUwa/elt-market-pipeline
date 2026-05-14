# ELK Market Data Pipeline

Real-time market data ingestion pipeline using
Elasticsearch and Kibana — the same stack used
by tier-1 banks for production monitoring.

Ingests live FX and equity market events,
detects anomalies, and visualizes data in Kibana.

## Business Context

Banks generate millions of market data events per day.
Production teams need to:
- Monitor price feeds in real time
- Detect anomalies (price spikes, latency issues)
- Alert on SLA breaches
- Visualize market activity for operations teams

This pipeline simulates that infrastructure:
market data producer → Elasticsearch → Kibana dashboard.

## Architecture

```
Market Data Producer (producer.py)
        ↓
Elasticsearch (port 9200)
        ↓
Kibana Dashboard (port 5601)
```

## Stack

```
Docker Compose
Elasticsearch 8.13
Kibana 8.13
Python + elasticsearch-py
```

## Run

```bash
# Start ELK stack
docker-compose up -d

# Wait ~60 seconds for Elasticsearch to start
# Then install dependencies and run producer
pip install -r requirements.txt
python producer.py          # continuous mode
python producer.py --once   # single batch
```

Kibana → http://localhost:5601

## Features

- Indexes FX and equity market events in real time
- Detects price spike anomalies (5% probability)
- Tracks execution latency per instrument
- Kibana-ready index mapping with proper field types
- ELK-compatible structured logging

## Instruments Monitored

EUR/USD · GBP/USD · USD/JPY · AAPL · SPX

## Kibana Setup

1. Go to http://localhost:5601
2. Stack Management → Index Patterns → Create
3. Pattern: `market-data*` → timestamp field: `@timestamp`
4. Discover → visualize your data
5. Dashboard → create panels for price, volume, anomalies

## Design Decisions

**Why no Logstash?**
For this demo, Python indexes directly to Elasticsearch.
In production: Logstash handles transformation and routing
from multiple data sources.

**Why single-node Elasticsearch?**
Sufficient for demo. Production uses 3+ node clusters
for high availability.

## Screenshots

![Kibana Dashboard](![img_2.png](img_2.png))
![Elasticsearch indexing](![img.png](img.png))
![Docker containers](![img_3.png](img_3.png))
![Producer logs](![img_1.png](img_1.png))

## Possible Improvements

- Add Logstash for data transformation
- Connect to real market feed (Bloomberg API)
- Add alerting rules in Kibana
- Deploy to Azure (AKS) for cloud-native demo
- Add Kafka for high-throughput ingestion