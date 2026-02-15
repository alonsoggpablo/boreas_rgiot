package main

import (
	"database/sql"
	"fmt"
	_ "github.com/lib/pq"
	"log"
	"os"
)

func main() {
	connStr := os.Getenv("PG_CONN")
	if connStr == "" {
		connStr = "postgres://boreas_user:boreas_password@db:5432/boreas_db?sslmode=disable"
	}
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatalf("Failed to connect to DB: %v", err)
	}
	defer db.Close()

	// Query Sigfox devices
	rows, err := db.Query("SELECT id, device_id FROM boreas_mediacion_sigfoxdevice")
	if err != nil {
		log.Fatalf("Query failed: %v", err)
	}
	defer rows.Close()

	for rows.Next() {
		var id int
		var deviceID string
		if err := rows.Scan(&id, &deviceID); err != nil {
			log.Printf("Row scan error: %v", err)
			continue
		}
		// TODO: Call sigfox API for deviceID
		fmt.Printf("Would call sigfox API for device_id %s (id %d)\n", deviceID, id)
	}
}
