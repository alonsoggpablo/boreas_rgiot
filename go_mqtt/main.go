package main

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

type Topic struct {
	Topic string `json:"topic"`
	QoS   int    `json:"qos"`
}

func fetchActiveTopics(apiURL string) ([]Topic, error) {
	resp, err := http.Get(apiURL)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var topics []Topic
	if err := json.NewDecoder(resp.Body).Decode(&topics); err != nil {
		return nil, err
	}
	return topics, nil
}

func main() {
		log.Printf("[DEBUG][STARTUP] main() has started and this is a fresh build.")
	log.SetFlags(0)
	log.SetOutput(os.Stdout)

	// (opts will be defined after all env vars are set)

	// Hardcoded credentials for testing
	mqttBroker := "ssl://mqtt.solutions-iot.es:8883"
	mqttUser := "boreas"
	mqttPass := "RGIoT"
	//topicAPI := "http://localhost:8000/api/topics/" // Example API URL, adjust as needed
	//dbConnStr := "host=localhost user=postgres password=postgres dbname=testdb sslmode=disable" // Example connection string

	fmt.Printf("MQTT_BROKER: %s\n", mqttBroker)
	fmt.Printf("MQTT_USERNAME: %s\n", mqttUser)
	fmt.Printf("MQTT_PASSWORD: %s\n", mqttPass)

	// No env var check needed, values are hardcoded for testing

	topicAPI := "http://web:8000/api/mqtt/active-topics/" // Django API service in Docker Compose
	topics, err := fetchActiveTopics(topicAPI)
	if err != nil {
		log.Fatalf("Failed to fetch topics: %v", err)
	}
	fmt.Println("Topics to subscribe:")
	for _, t := range topics {
		fmt.Printf("  - %s (QoS %d)\n", t.Topic, t.QoS)
	}
	// Connect to DB for storing last reads
	dbConnStr := "host=db user=boreas_user password=boreas_password dbname=boreas_db sslmode=disable"
	deviceMapPath := os.Getenv("DEVICE_MAP_PATH")
	if deviceMapPath == "" {
		deviceMapPath = "/app/media/external_devices_map.json"
	}
	       dbw, err := NewDBWriter(dbConnStr, deviceMapPath)
	       if err != nil {
		       log.Fatalf("Failed to connect to DB: %v", err)
	       }
		fmt.Printf("[DEBUG][MAIN] DBWriter created, deviceMapPath: '%s'\n", deviceMapPath)

	// MQTT client setup
	opts := mqtt.NewClientOptions().AddBroker(mqttBroker)
	opts.SetProtocolVersion(4)
	hostname, _ := os.Hostname()
	uniqueID := fmt.Sprintf("go_mqtt_%s_%d", hostname, time.Now().UnixNano())
	opts.SetClientID(uniqueID)
	fmt.Printf("Using MQTT ClientID: %s\n", uniqueID)
	if mqttUser != "" {
		opts.SetUsername(mqttUser)
		opts.SetPassword(mqttPass)
	}
	useTLS := strings.HasSuffix(mqttBroker, ":8883") ||
		strings.HasPrefix(mqttBroker, "ssl://") ||
		strings.HasPrefix(mqttBroker, "tls://")
	if useTLS {
		tlsConfig := &tls.Config{
			InsecureSkipVerify: true,
		}
		opts.SetTLSConfig(tlsConfig)
	}

	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		log.Fatalf("MQTT connect error: %v", token.Error())
	}
	defer client.Disconnect(250)

	// Subscribe to all topics from API
	received := make(chan bool)
	for _, t := range topics {
		topic := t.Topic
		qos := byte(t.QoS)
		token := client.Subscribe(topic, qos, func(client mqtt.Client, msg mqtt.Message) {
			   log.Printf("[DEBUG][RECV] Raw MQTT message received. Topic: '%s', Payload: '%s'", msg.Topic(), string(msg.Payload()))
			// Try to extract deviceID from payload (idema for AEMET), else from topic
			deviceID := "unknown"
			payload := string(msg.Payload())
			// Try to parse idema from JSON payload
			// Try AEMET idema, then device_info.uuid, then topic logic
			type aemetPayload struct {
				Idema string `json:"idema"`
			}
			var ap aemetPayload
			if err := json.Unmarshal(msg.Payload(), &ap); err == nil && ap.Idema != "" {
				deviceID = ap.Idema
			} else {
				// Try device_info.uuid
				var payloadMap map[string]interface{}
				if err := json.Unmarshal(msg.Payload(), &payloadMap); err == nil {
					if devInfo, ok := payloadMap["device_info"].(map[string]interface{}); ok {
						if uuid, ok := devInfo["uuid"].(string); ok && uuid != "" {
							deviceID = uuid
						}
					}
				}
				// If still unknown, use topic logic
				if deviceID == "unknown" {
					parts := strings.Split(msg.Topic(), "/")
					if len(parts) > 3 && parts[0] == "RESP" && parts[1] == "tactica" && parts[2] == "shelly2" {
						deviceID = parts[3]
					} else if len(parts) > 1 {
						deviceID = parts[1]
					} else if len(parts) > 0 {
						deviceID = parts[0]
					}
				}
			}
			   log.Printf("[DEBUG][MSG] Topic: '%s', deviceID: '%s' (hex: %x)", msg.Topic(), deviceID, deviceID)
			   err := dbw.UpsertReportedMeasure(msg.Topic(), deviceID, payload)
			if err != nil {
				log.Printf("DB upsert error (reported_measure) for %s: %v", msg.Topic(), err)
			}
			// Optionally, signal received for test/demo
			// received <- true
		})
		if token.Wait() && token.Error() != nil {
			log.Printf("Subscribe error for %s: %v", topic, token.Error())
		} else {
			fmt.Printf("Successfully subscribed to %s\n", topic)
		}
	}

	// Wait for a message or timeout (optional demo logic)
	select {
	case <-received:
		fmt.Println("Message received, exiting.")
	case <-time.After(30 * time.Second):
		fmt.Println("No message received in 30 seconds, exiting.")
	}
}
