package main

import (
	"context"
	"database/sql"
	"log"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

type DBWriter struct {
	db          *sql.DB
	familyCache map[string]int
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
	w := &DBWriter{db: db, familyCache: make(map[string]int)}
	if err := w.RefreshFamilyCache(); err != nil {
		return nil, err
	}
	go w.PeriodicFamilyCacheRefresh()
	return w, nil
}

func (w *DBWriter) RefreshFamilyCache() error {
	rows, err := w.db.Query("SELECT id, name FROM boreas_mediacion_mqtt_device_family")
	if err != nil {
		return err
	}
	defer rows.Close()
	cache := make(map[string]int)
	for rows.Next() {
		var id int
		var name string
		if err := rows.Scan(&id, &name); err != nil {
			return err
		}
		cache[name] = id
	}
	w.familyCache = cache
	return nil
}

func (w *DBWriter) PeriodicFamilyCacheRefresh() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()
	for range ticker.C {
		_ = w.RefreshFamilyCache()
	}
}

// Upsert last message for topic/device_id in reported_measure
func (w *DBWriter) UpsertReportedMeasure(topic, deviceID, payload string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	deviceJSON := `{"device_id": "` + deviceID + `"}`
	// Extract family name from topic (first segment)
	familyName := ""
	parts := strings.SplitN(topic, "/", 2)
	if len(parts) > 0 {
		familyName = parts[0]
	}
	familyID, ok := w.familyCache[familyName]
	if !ok {
		log.Printf("[WARN] Family name '%s' not found in cache, setting familyID=0", familyName)
		familyID = 0 // or NULL if you want
	} else {
		log.Printf("[INFO] Using family name '%s' with ID %d", familyName, familyID)
	}
	query := `INSERT INTO boreas_mediacion_reported_measure (feed, device_id, device, measures, report_time, device_family_id_id)
		 VALUES ($1, $2, $3, $4, NOW(), $5)
		 ON CONFLICT (feed, device_id)
		 DO UPDATE SET device = $3, measures = $4, report_time = NOW(), device_family_id_id = $5;`
	_, err := w.db.ExecContext(ctx, query, topic, deviceID, deviceJSON, payload, familyID)
	return err
}
