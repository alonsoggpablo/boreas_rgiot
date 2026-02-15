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

	// Query supplies for datadis
	rows, err := db.Query("SELECT id, cups FROM boreas_mediacion_datadissupply WHERE active = true")
	if err != nil {
		log.Fatalf("Query failed: %v", err)
	}
	defer rows.Close()

	for rows.Next() {
		var id int
		var cups string
		if err := rows.Scan(&id, &cups); err != nil {
			log.Printf("Row scan error: %v", err)
			continue
		}
		// TODO: Call datadis API for cups
		fmt.Printf("Would call datadis API for CUPS %s (id %d)\n", cups, id)
	}
}
