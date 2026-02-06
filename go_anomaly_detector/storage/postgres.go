package storage

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	_ "github.com/lib/pq"
)

type PostgresStore struct {
	db *sql.DB
}

type ReportedMeasure struct {
	ID             int
	ReportTime     time.Time
	DeviceID       string
	NanoenviName   sql.NullString
	NanoenviClient sql.NullString
	Feed           string
	Measures       interface{} // Can be map[string]interface{} or primitive value
}

type Anomaly struct {
	DeviceName   string
	DeviceID     string
	Client       string
	MetricName   string
	MetricValue  float64
	AnomalyType  string
	Severity     float64
	BaselineMean float64
	BaselineStd  float64
	DetectedAt   time.Time
	Details      map[string]interface{}
}

func NewPostgresStore(connStr string) (*PostgresStore, error) {
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &PostgresStore{db: db}, nil
}

func (s *PostgresStore) Close() error {
	return s.db.Close()
}

// GetRecentMeasures fetches reported_measure records from the last N hours
func (s *PostgresStore) GetRecentMeasures(ctx context.Context, hours int) ([]ReportedMeasure, error) {
	query := `
		SELECT id, report_time, device_id, nanoenvi_name, nanoenvi_client, feed, measures
		FROM boreas_mediacion_reported_measure
		WHERE report_time >= NOW() - INTERVAL '%d hours'
		ORDER BY report_time DESC
	`

	rows, err := s.db.QueryContext(ctx, fmt.Sprintf(query, hours))
	if err != nil {
		return nil, fmt.Errorf("query failed: %w", err)
	}
	defer rows.Close()

	var measures []ReportedMeasure
	for rows.Next() {
		var m ReportedMeasure
		var measuresJSON []byte

		err := rows.Scan(&m.ID, &m.ReportTime, &m.DeviceID, &m.NanoenviName, &m.NanoenviClient, &m.Feed, &measuresJSON)
		if err != nil {
			return nil, fmt.Errorf("scan failed: %w", err)
		}

		// Try to unmarshal as interface{} to handle both objects and primitives
		var measuresData interface{}
		if err := json.Unmarshal(measuresJSON, &measuresData); err != nil {
			return nil, fmt.Errorf("failed to unmarshal measures: %w", err)
		}
		m.Measures = measuresData

		measures = append(measures, m)
	}

	return measures, rows.Err()
}

// StoreAnomaly stores a detected anomaly in the database
func (s *PostgresStore) StoreAnomaly(ctx context.Context, anomaly Anomaly) error {
	// Create anomalies table if it doesn't exist
	createTableSQL := `
		CREATE TABLE IF NOT EXISTS boreas_mediacion_detected_anomaly (
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
	`
	if _, err := s.db.ExecContext(ctx, createTableSQL); err != nil {
		return fmt.Errorf("failed to create anomalies table: %w", err)
	}

	// Create index if it doesn't exist
	createIndexSQL := `
		CREATE INDEX IF NOT EXISTS idx_anomaly_device_metric 
		ON boreas_mediacion_detected_anomaly(device_id, metric_name, detected_at DESC);
	`
	if _, err := s.db.ExecContext(ctx, createIndexSQL); err != nil {
		return fmt.Errorf("failed to create index: %w", err)
	}

	detailsJSON, err := json.Marshal(anomaly.Details)
	if err != nil {
		return fmt.Errorf("failed to marshal details: %w", err)
	}

	insertSQL := `
		INSERT INTO boreas_mediacion_detected_anomaly 
		(device_name, device_id, client, metric_name, metric_value, anomaly_type, 
		 severity, baseline_mean, baseline_std, detected_at, details, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
	`

	_, err = s.db.ExecContext(ctx, insertSQL,
		anomaly.DeviceName,
		anomaly.DeviceID,
		anomaly.Client,
		anomaly.MetricName,
		anomaly.MetricValue,
		anomaly.AnomalyType,
		anomaly.Severity,
		anomaly.BaselineMean,
		anomaly.BaselineStd,
		anomaly.DetectedAt,
		detailsJSON,
	)

	return err
}

// GetRecentAnomalies retrieves recent anomalies for reporting
func (s *PostgresStore) GetRecentAnomalies(ctx context.Context, since time.Time) ([]Anomaly, error) {
	query := `
		SELECT device_name, device_id, client, metric_name, metric_value, 
		       anomaly_type, severity, baseline_mean, baseline_std, detected_at, details
		FROM boreas_mediacion_detected_anomaly
		WHERE detected_at >= $1
		ORDER BY detected_at DESC
		LIMIT 100
	`

	rows, err := s.db.QueryContext(ctx, query, since)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var anomalies []Anomaly
	for rows.Next() {
		var a Anomaly
		var detailsJSON []byte

		err := rows.Scan(&a.DeviceName, &a.DeviceID, &a.Client, &a.MetricName,
			&a.MetricValue, &a.AnomalyType, &a.Severity, &a.BaselineMean,
			&a.BaselineStd, &a.DetectedAt, &detailsJSON)
		if err != nil {
			return nil, err
		}

		if err := json.Unmarshal(detailsJSON, &a.Details); err == nil {
			a.Details = make(map[string]interface{})
		}

		anomalies = append(anomalies, a)
	}

	return anomalies, rows.Err()
}
