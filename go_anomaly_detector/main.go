package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"go_anomaly_detector/detector"
	"go_anomaly_detector/storage"
)

func main() {
	log.Println("Starting Boreas Anomaly Detection Agent...")

	// Configuration from environment
	pgConn := getEnv("PG_CONN", "postgres://boreas_user:boreas_password@db:5432/boreas_db?sslmode=disable")
	parquetDir := getEnv("PARQUET_DIR", "/app/data/reported_measures_archive")
	checkInterval := getEnvDuration("CHECK_INTERVAL", 5*time.Minute)
	baselineDays := getEnvInt("BASELINE_DAYS", 7)

	// Initialize storage
	store, err := storage.NewPostgresStore(pgConn)
	if err != nil {
		log.Fatalf("Failed to connect to PostgreSQL: %v", err)
	}
	defer store.Close()

	// Initialize detector
	det := detector.NewDetector(store, parquetDir, baselineDays)

	log.Printf("Configuration:")
	log.Printf("  PostgreSQL: %s", pgConn)
	log.Printf("  Parquet Dir: %s", parquetDir)
	log.Printf("  Check Interval: %v", checkInterval)
	log.Printf("  Baseline Days: %d", baselineDays)

	// Run detection loop
	ctx := context.Background()
	ticker := time.NewTicker(checkInterval)
	defer ticker.Stop()

	// Run immediately on startup
	runDetection(ctx, det)

	// Then run on schedule
	for {
		select {
		case <-ticker.C:
			runDetection(ctx, det)
		case <-ctx.Done():
			log.Println("Shutting down...")
			return
		}
	}
}

func runDetection(ctx context.Context, det *detector.Detector) {
	log.Println("\n" + "===========================================")
	log.Println("Running anomaly detection...")
	log.Println("===========================================")

	start := time.Now()
	results, err := det.DetectAnomalies(ctx)
	if err != nil {
		log.Printf("Error during detection: %v", err)
		return
	}

	duration := time.Since(start)
	log.Printf("\n✓ Detection complete in %v", duration)
	log.Printf("  Devices checked: %d", results.DevicesChecked)
	log.Printf("  Metrics analyzed: %d", results.MetricsAnalyzed)
	log.Printf("  Anomalies detected: %d", results.AnomaliesDetected)

	if results.AnomaliesDetected > 0 {
		log.Printf("\nRecent anomalies:")
		for _, a := range results.RecentAnomalies {
			log.Printf("  [%s] %s/%s: %s (severity: %.2f)",
				a.DetectedAt.Format("15:04:05"),
				a.DeviceName,
				a.MetricName,
				a.AnomalyType,
				a.Severity)
		}
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if d, err := time.ParseDuration(value); err == nil {
			return d
		}
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		var i int
		if n, err := fmt.Sscanf(value, "%d", &i); err == nil && n == 1 {
			return i
		}
	}
	return defaultValue
}
