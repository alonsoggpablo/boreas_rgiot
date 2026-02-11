package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	_ "github.com/lib/pq"
)

type DBWriter struct {
	db          *sql.DB
	familyCache map[string]int
	deviceMap   map[string]DeviceInfo
	deviceMu    sync.RWMutex
	devicePath  string
}

type DeviceInfo struct {
	Name   *string `json:"name"`
	Client *string `json:"client"`
	Source string  `json:"source"`
}

type deviceMapPayload struct {
	Devices map[string]DeviceInfo `json:"devices"`
}

func NewDBWriter(connStr, deviceMapPath string) (*DBWriter, error) {
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, err
	}
	// Test connection
	if err := db.Ping(); err != nil {
		return nil, err
	}
	w := &DBWriter{
		db:          db,
		familyCache: make(map[string]int),
		deviceMap:   make(map[string]DeviceInfo),
		devicePath:  deviceMapPath,
	}
	if err := w.RefreshFamilyCache(); err != nil {
		return nil, err
	}
	if err := w.RefreshDeviceMap(); err != nil {
		log.Printf("[WARN] device map load failed: %v", err)
	}
	go w.PeriodicFamilyCacheRefresh()
	go w.PeriodicDeviceMapRefresh()
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

func (w *DBWriter) RefreshDeviceMap() error {
	if w.devicePath == "" {
		return nil
	}
	data, err := os.ReadFile(w.devicePath)
	if err != nil {
		return err
	}
	var payload deviceMapPayload
	if err := json.Unmarshal(data, &payload); err != nil {
		return err
	}
	if payload.Devices == nil {
		payload.Devices = make(map[string]DeviceInfo)
	}
	w.deviceMu.Lock()
	w.deviceMap = payload.Devices
	w.deviceMu.Unlock()
	return nil
}

func (w *DBWriter) PeriodicDeviceMapRefresh() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()
	for range ticker.C {
		if err := w.RefreshDeviceMap(); err != nil {
			log.Printf("[WARN] device map refresh failed: %v", err)
		}
	}
}

func (w *DBWriter) lookupDeviceInfo(deviceID string) (DeviceInfo, bool) {
	w.deviceMu.RLock()
	info, ok := w.deviceMap[deviceID]
	w.deviceMu.RUnlock()
	return info, ok
}

// Upsert last message for topic/device_id in reported_measure
func (w *DBWriter) UpsertReportedMeasure(topic, deviceID, payload string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	deviceJSON := `{"device_id": "` + deviceID + `"}`
	var nanoUUID *string
	var nanoName *string
	var nanoClient *string
	if info, ok := w.lookupDeviceInfo(deviceID); ok {
		nanoUUID = &deviceID
		nanoName = info.Name
		nanoClient = info.Client
	}
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
	       query := `INSERT INTO boreas_mediacion_reported_measure (
		       feed, device_id, device, measures, report_time, device_family_id_id,
		       uuid, name, client
	       ) VALUES ($1, $2, $3, $4, NOW(), $5, $6, $7, $8);`
	       _, err := w.db.ExecContext(ctx, query, topic, deviceID, deviceJSON, payload, familyID, nanoUUID, nanoName, nanoClient)
	return err
}
