package detector

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"time"

	"go_anomaly_detector/parquet"
	"go_anomaly_detector/storage"
)

type Detector struct {
	store        *storage.PostgresStore
	parquetDir   string
	baselineDays int
}

type DetectionResult struct {
	DevicesChecked    int
	MetricsAnalyzed   int
	AnomaliesDetected int
	RecentAnomalies   []storage.Anomaly
}

type MetricStats struct {
	Mean   float64
	StdDev float64
	Min    float64
	Max    float64
	Count  int
}

func NewDetector(store *storage.PostgresStore, parquetDir string, baselineDays int) *Detector {
	return &Detector{
		store:        store,
		parquetDir:   parquetDir,
		baselineDays: baselineDays,
	}
}

// DetectAnomalies runs the full anomaly detection pipeline
func (d *Detector) DetectAnomalies(ctx context.Context) (*DetectionResult, error) {
	result := &DetectionResult{}

	// Get recent measures (last 1 hour)
	measures, err := d.store.GetRecentMeasures(ctx, 1)
	if err != nil {
		return nil, fmt.Errorf("failed to get recent measures: %w", err)
	}

	if len(measures) == 0 {
		log.Println("No recent measures found")
		return result, nil
	}

	// Group by device and metric
	deviceMetrics := d.groupByDeviceMetric(measures)
	result.DevicesChecked = len(deviceMetrics)

	// Load historical baselines from Parquet files
	log.Printf("Loading baselines from Parquet files (%d days)...", d.baselineDays)
	baselines, err := d.loadHistoricalBaselines()
	if err != nil {
		log.Printf("Warning: Failed to load Parquet baselines: %v. Using recent data only.", err)
		baselines = d.calculateBaselines(measures)
	} else {
		log.Printf("✓ Loaded baselines for %d device/metric combinations", len(baselines))
	}

	// Detect anomalies
	anomaliesDetected := 0
	for deviceKey, metrics := range deviceMetrics {
		for metricName, values := range metrics {
			result.MetricsAnalyzed++

			baseline, exists := baselines[deviceKey+":"+metricName]
			if !exists || baseline.Count < 10 {
				continue // Need minimum data for baseline
			}

			// Check each value for anomalies
			for _, measure := range values {
				metricValue := d.extractMetricValue(measure.Measures, metricName)
				if metricValue == nil {
					continue
				}

				anomaly := d.detectStatisticalAnomaly(measure, metricName, *metricValue, baseline)
				if anomaly != nil {
					if err := d.store.StoreAnomaly(ctx, *anomaly); err != nil {
						log.Printf("Failed to store anomaly: %v", err)
					} else {
						anomaliesDetected++
					}
				}
			}
		}
	}

	result.AnomaliesDetected = anomaliesDetected

	// Get recent anomalies for reporting
	since := time.Now().Add(-1 * time.Hour)
	recentAnomalies, err := d.store.GetRecentAnomalies(ctx, since)
	if err == nil {
		result.RecentAnomalies = recentAnomalies
	}

	return result, nil
}

// groupByDeviceMetric organizes measures by device and metric name
func (d *Detector) groupByDeviceMetric(measures []storage.ReportedMeasure) map[string]map[string][]storage.ReportedMeasure {
	grouped := make(map[string]map[string][]storage.ReportedMeasure)

	for _, measure := range measures {
		deviceKey := measure.DeviceID
		if measure.NanoenviName.Valid && measure.NanoenviName.String != "" {
			deviceKey = measure.NanoenviName.String
		}

		if grouped[deviceKey] == nil {
			grouped[deviceKey] = make(map[string][]storage.ReportedMeasure)
		}

		// Handle both object and primitive measure types
		if measuresMap, ok := measure.Measures.(map[string]interface{}); ok {
			// Object type: extract metric names from measures array
			if measuresData, ok := measuresMap["measures"].([]interface{}); ok {
				for _, m := range measuresData {
					if metricMap, ok := m.(map[string]interface{}); ok {
						if metricName, ok := metricMap["n"].(string); ok {
							grouped[deviceKey][metricName] = append(grouped[deviceKey][metricName], measure)
						}
					}
				}
			}
		} else {
			// Primitive type: use feed as metric name
			metricName := measure.Feed
			grouped[deviceKey][metricName] = append(grouped[deviceKey][metricName], measure)
		}
	}

	return grouped
}

// calculateBaselines computes statistical baselines for each device/metric combination
func (d *Detector) calculateBaselines(measures []storage.ReportedMeasure) map[string]MetricStats {
	baselines := make(map[string]MetricStats)
	valuesByKey := make(map[string][]float64)

	// Collect all values
	for _, measure := range measures {
		deviceKey := measure.DeviceID
		if measure.NanoenviName.Valid && measure.NanoenviName.String != "" {
			deviceKey = measure.NanoenviName.String
		}

		// Handle both object and primitive measure types
		if measuresMap, ok := measure.Measures.(map[string]interface{}); ok {
			// Object type: extract metrics from measures array
			if measuresData, ok := measuresMap["measures"].([]interface{}); ok {
				for _, m := range measuresData {
					if metricMap, ok := m.(map[string]interface{}); ok {
						metricName, _ := metricMap["n"].(string)
						if value := d.parseFloat(metricMap["v"]); value != nil {
							key := deviceKey + ":" + metricName
							valuesByKey[key] = append(valuesByKey[key], *value)
						}
					}
				}
			}
		} else {
			// Primitive type: use the value directly
			if value := d.parseFloat(measure.Measures); value != nil {
				key := deviceKey + ":" + measure.Feed
				valuesByKey[key] = append(valuesByKey[key], *value)
			}
		}
	}

	// Calculate statistics
	for key, values := range valuesByKey {
		if len(values) < 3 {
			continue
		}

		stats := MetricStats{
			Count: len(values),
			Min:   values[0],
			Max:   values[0],
		}

		// Calculate mean
		sum := 0.0
		for _, v := range values {
			sum += v
			if v < stats.Min {
				stats.Min = v
			}
			if v > stats.Max {
				stats.Max = v
			}
		}
		stats.Mean = sum / float64(len(values))

		// Calculate standard deviation
		variance := 0.0
		for _, v := range values {
			diff := v - stats.Mean
			variance += diff * diff
		}
		stats.StdDev = math.Sqrt(variance / float64(len(values)))

		baselines[key] = stats
	}

	return baselines
}

// detectStatisticalAnomaly checks if a value is anomalous using z-score
func (d *Detector) detectStatisticalAnomaly(measure storage.ReportedMeasure, metricName string, value float64, baseline MetricStats) *storage.Anomaly {
	if baseline.StdDev == 0 {
		return nil // No variation in baseline
	}

	// Calculate z-score
	zScore := math.Abs((value - baseline.Mean) / baseline.StdDev)

	// Threshold: 3 standard deviations (99.7% confidence)
	if zScore > 3.0 {
		deviceName := ""
		if measure.NanoenviName.Valid {
			deviceName = measure.NanoenviName.String
		}
		client := ""
		if measure.NanoenviClient.Valid {
			client = measure.NanoenviClient.String
		}
		return &storage.Anomaly{
			DeviceName:   deviceName,
			DeviceID:     measure.DeviceID,
			Client:       client,
			MetricName:   metricName,
			MetricValue:  value,
			AnomalyType:  "statistical_outlier",
			Severity:     zScore,
			BaselineMean: baseline.Mean,
			BaselineStd:  baseline.StdDev,
			DetectedAt:   measure.ReportTime,
			Details: map[string]interface{}{
				"z_score":        zScore,
				"baseline_min":   baseline.Min,
				"baseline_max":   baseline.Max,
				"baseline_count": baseline.Count,
			},
		}
	}

	return nil
}

// extractMetricValue extracts a specific metric value from measures JSON
func (d *Detector) extractMetricValue(measures interface{}, metricName string) *float64 {
	// Handle object type
	if measuresMap, ok := measures.(map[string]interface{}); ok {
		if measuresData, ok := measuresMap["measures"].([]interface{}); ok {
			for _, m := range measuresData {
				if metricMap, ok := m.(map[string]interface{}); ok {
					if name, _ := metricMap["n"].(string); name == metricName {
						return d.parseFloat(metricMap["v"])
					}
				}
			}
		}
	} else {
		// Handle primitive type - return the value directly
		return d.parseFloat(measures)
	}
	return nil
}

// parseFloat safely converts interface{} to float64
func (d *Detector) parseFloat(v interface{}) *float64 {
	switch val := v.(type) {
	case float64:
		return &val
	case float32:
		f := float64(val)
		return &f
	case int:
		f := float64(val)
		return &f
	case int64:
		f := float64(val)
		return &f
	case int32:
		f := float64(val)
		return &f
	case uint:
		f := float64(val)
		return &f
	case uint64:
		f := float64(val)
		return &f
	case uint32:
		f := float64(val)
		return &f
	case bool:
		// Convert bool to 0 or 1
		if val {
			f := 1.0
			return &f
		}
		f := 0.0
		return &f
	case string:
		var f float64
		if _, err := fmt.Sscanf(val, "%f", &f); err == nil {
			return &f
		}
	}
	return nil
}

// loadHistoricalBaselines loads baselines from Parquet archive files
func (d *Detector) loadHistoricalBaselines() (map[string]MetricStats, error) {
	reader := parquet.NewParquetReader(d.parquetDir)

	// Calculate date range: last N days
	endDate := time.Now().AddDate(0, 0, -1) // Yesterday (data is archived)
	startDate := endDate.AddDate(0, 0, -d.baselineDays)

	log.Printf("Reading Parquet files from %s to %s", startDate.Format("2006-01-02"), endDate.Format("2006-01-02"))

	records, err := reader.ReadDateRange(startDate, endDate)
	if err != nil {
		return nil, fmt.Errorf("failed to read Parquet files: %w", err)
	}

	if len(records) == 0 {
		return nil, fmt.Errorf("no historical data found in Parquet files")
	}

	log.Printf("Loaded %d records from Parquet files", len(records))

	// Convert Parquet records to measures and calculate baselines
	valuesByKey := make(map[string][]float64)

	for _, record := range records {
		deviceKey := record.DeviceID
		if record.NanoenviName != "" {
			deviceKey = record.NanoenviName
		}

		// Parse measures JSON
		var measures map[string]interface{}
		if err := json.Unmarshal([]byte(record.Measures), &measures); err != nil {
			continue
		}

		// Extract metrics
		if measuresData, ok := measures["measures"].([]interface{}); ok {
			for _, m := range measuresData {
				if metricMap, ok := m.(map[string]interface{}); ok {
					metricName, _ := metricMap["n"].(string)
					if value := d.parseFloat(metricMap["v"]); value != nil {
						key := deviceKey + ":" + metricName
						valuesByKey[key] = append(valuesByKey[key], *value)
					}
				}
			}
		}
	}

	// Calculate statistics
	baselines := make(map[string]MetricStats)
	for key, values := range valuesByKey {
		if len(values) < 3 {
			continue
		}

		stats := MetricStats{
			Count: len(values),
			Min:   values[0],
			Max:   values[0],
		}

		// Calculate mean
		sum := 0.0
		for _, v := range values {
			sum += v
			if v < stats.Min {
				stats.Min = v
			}
			if v > stats.Max {
				stats.Max = v
			}
		}
		stats.Mean = sum / float64(len(values))

		// Calculate standard deviation
		variance := 0.0
		for _, v := range values {
			diff := v - stats.Mean
			variance += diff * diff
		}
		stats.StdDev = math.Sqrt(variance / float64(len(values)))

		baselines[key] = stats
	}

	return baselines, nil
}
