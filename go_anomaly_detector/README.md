# Boreas Anomaly Detection Agent

Go-based service for detecting anomalies in IoT sensor data from reported_measure table.

## Features

- **Statistical anomaly detection**: Z-score based outlier detection (3σ threshold)
- **Per-device/metric baselines**: Individual normal ranges for each device and metric
- **Historical data support**: Reads Parquet archives for baseline calculation
- **Real-time processing**: Analyzes recent PostgreSQL data every 5 minutes
- **Anomaly storage**: Stores detected anomalies in `boreas_mediacion_detected_anomaly` table

## Architecture

```
┌─────────────────┐
│  PostgreSQL     │◄─── Real-time data (last 7 days)
│  reported_      │
│  measure        │
└────────┬────────┘
         │
         ▼
    ┌────────────┐
    │  Anomaly   │
    │  Detector  │
    └────┬───────┘
         │
         ▼
┌─────────────────┐
│  Parquet Files  │◄─── Historical baselines (7-30+ days)
│  Archive        │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  detected_      │
│  anomaly table  │
└─────────────────┘
```

## Configuration

Environment variables:

- `PG_CONN`: PostgreSQL connection string (default: `postgres://boreas_user:boreas_password@db:5432/boreas_db?sslmode=disable`)
- `PARQUET_DIR`: Directory with Parquet archives (default: `/app/data/reported_measures_archive`)
- `CHECK_INTERVAL`: Detection interval (default: `5m`)
- `BASELINE_DAYS`: Days of historical data for baseline (default: `7`)

## Running

### Docker

```bash
docker build -t go_anomaly_detector .
docker run -e PG_CONN="postgres://..." go_anomaly_detector
```

### Standalone

```bash
go mod download
go run main.go
```

## Anomaly Types

Currently implemented:
- `statistical_outlier`: Value exceeds 3 standard deviations from baseline mean

Future enhancements:
- `sudden_change`: Rapid increase/decrease
- `missing_data`: Device stopped reporting
- `threshold_breach`: Domain-specific limits (e.g., PM10 > 150)

## Database Schema

```sql
CREATE TABLE boreas_mediacion_detected_anomaly (
    id SERIAL PRIMARY KEY,
    device_name VARCHAR(255),
    device_id VARCHAR(100),
    client VARCHAR(255),
    metric_name VARCHAR(100),
    metric_value DOUBLE PRECISION,
    anomaly_type VARCHAR(50),
    severity DOUBLE PRECISION,
    baseline_mean DOUBLE PRECISION,
    baseline_std DOUBLE PRECISION,
    detected_at TIMESTAMP,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Integration

- **Grafana**: Query `detected_anomaly` table for dashboard annotations
- **Alerts**: Trigger notifications based on anomaly severity
- **Reports**: Historical anomaly analysis for device health monitoring
