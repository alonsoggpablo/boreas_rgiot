package main

import (
	"context"
	"database/sql"
	_ "github.com/lib/pq"
	"time"
)

type DBWriter struct {
	db *sql.DB
}

func NewDBWriter(connStr string) (*DBWriter, error) {
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, err
	}
	// Test connection
	if err := db.Ping(); err != nil {
		return nil, err
	}
	return &DBWriter{db: db}, nil
}

// Upsert last message for topic/device_id in reported_measure
func (w *DBWriter) UpsertReportedMeasure(topic, deviceID, payload string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	// For now, store device as a minimal JSON with device_id (could be extended)
	deviceJSON := `{"device_id": "` + deviceID + `"}`
	query := `INSERT INTO boreas_mediacion_reported_measure (feed, device_id, device, measures, report_time)
	   VALUES ($1, $2, $3, $4, NOW())
	   ON CONFLICT (feed, device_id)
	   DO UPDATE SET device = $3, measures = $4, report_time = NOW();`
	_, err := w.db.ExecContext(ctx, query, topic, deviceID, deviceJSON, payload)
	return err
}


