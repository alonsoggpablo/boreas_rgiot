-- set_retention_policy.sql
-- This script sets a 2-hour retention policy for the TimescaleDB hypertable 'boreas_mediacion_reported_measures'.

SELECT add_retention_policy('boreas_mediacion_reported_measures', INTERVAL '2 hours');
