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

	// Query WirelessLogic SIMs
	rows, err := db.Query("SELECT id, iccid FROM boreas_mediacion_wirelesslogic_sim")
	if err != nil {
		log.Fatalf("Query failed: %v", err)
	}
	defer rows.Close()

	for rows.Next() {
		var id int
		var iccid string
		if err := rows.Scan(&id, &iccid); err != nil {
			log.Printf("Row scan error: %v", err)
			continue
		}
		// TODO: Call wireless API for iccid
		fmt.Printf("Would call wireless API for ICCID %s (id %d)\n", iccid, id)
	}
}
