package parquet

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/parquet-go/parquet-go"
)

// ReportedMeasureRecord represents a row in the Parquet file
type ReportedMeasureRecord struct {
	ID             int64     `parquet:"id"`
	ReportTime     time.Time `parquet:"report_time"`
	DeviceID       string    `parquet:"device_id"`
	NanoenviName   string    `parquet:"nanoenvi_name"`
	NanoenviClient string    `parquet:"nanoenvi_client"`
	Feed           string    `parquet:"feed"`
	Measures       string    `parquet:"measures"` // JSON as string
}

type ParquetReader struct {
	baseDir string
}

func NewParquetReader(baseDir string) *ParquetReader {
	return &ParquetReader{baseDir: baseDir}
}

// ReadDateRange reads all Parquet files in a date range
func (pr *ParquetReader) ReadDateRange(startDate, endDate time.Time) ([]ReportedMeasureRecord, error) {
	var allRecords []ReportedMeasureRecord

	currentDate := startDate
	for currentDate.Before(endDate) || currentDate.Equal(endDate) {
		dateStr := currentDate.Format("2006-01-02")
		filename := fmt.Sprintf("reported_measures_%s.parquet", dateStr)
		filepath := filepath.Join(pr.baseDir, filename)

		// Check if file exists
		if _, err := os.Stat(filepath); os.IsNotExist(err) {
			currentDate = currentDate.AddDate(0, 0, 1)
			continue
		}

		records, err := pr.readFile(filepath)
		if err != nil {
			return nil, fmt.Errorf("failed to read %s: %w", filename, err)
		}

		allRecords = append(allRecords, records...)
		currentDate = currentDate.AddDate(0, 0, 1)
	}

	return allRecords, nil
}

// readFile reads a single Parquet file
func (pr *ParquetReader) readFile(filepath string) ([]ReportedMeasureRecord, error) {
	file, err := os.Open(filepath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := parquet.NewReader(file)
	defer reader.Close()

	var records []ReportedMeasureRecord
	for {
		var record ReportedMeasureRecord
		err := reader.Read(&record)
		if err != nil {
			break
		}
		records = append(records, record)
	}

	return records, nil
}

// GetAvailableDates returns list of dates with Parquet files
func (pr *ParquetReader) GetAvailableDates() ([]time.Time, error) {
	files, err := filepath.Glob(filepath.Join(pr.baseDir, "reported_measures_*.parquet"))
	if err != nil {
		return nil, err
	}

	var dates []time.Time
	for _, file := range files {
		basename := filepath.Base(file)
		// Extract date from filename: reported_measures_2026-02-06.parquet
		dateStr := basename[18:28] // YYYY-MM-DD
		date, err := time.Parse("2006-01-02", dateStr)
		if err != nil {
			continue
		}
		dates = append(dates, date)
	}

	return dates, nil
}
