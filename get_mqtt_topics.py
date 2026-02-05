#!/usr/bin/env python3
"""
Script to retrieve all MQTT topics by subscribing to broker.
Listens for messages on all topics (#) and dumps unique topics to file.
"""

import paho.mqtt.client as mqtt
import json
import sys
from datetime import datetime
from pathlib import Path

# Configuration
BROKER_HOST = "mqtt.solutions-iot.es"
BROKER_PORT = 8883
BROKER_USERNAME = "boreas"
BROKER_PASSWORD = "RGIoT"
LISTEN_DURATION = 30  # seconds
OUTPUT_FILE = "mqtt_topics_discovered.txt"
OUTPUT_JSON = "mqtt_topics_discovered.json"
USE_TLS = True

topics_set = set()
message_count = 0

def on_connect(client, userdata, flags, rc):
    """Callback for when client connects to broker"""
    if rc == 0:
        print("✓ Connected to MQTT broker")
        print(f"Subscribing to all topics (#)...")
        client.subscribe("#")
    else:
        print(f"❌ Connection failed with code {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback for when a message is received"""
    global message_count
    topics_set.add(msg.topic)
    message_count += 1
    
    if message_count % 10 == 0:
        print(f"  Captured {len(topics_set)} unique topics ({message_count} messages)...", end='\r')

def on_disconnect(client, userdata, rc):
    """Callback for when client disconnects"""
    if rc != 0:
        print(f"Unexpected disconnection: {rc}")

def save_to_file(topics, filename):
    """Save topics to text file"""
    with open(filename, 'w') as f:
        f.write(f"MQTT Topics Discovered\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Listen duration: {LISTEN_DURATION} seconds\n")
        f.write(f"Broker: {BROKER_HOST}:{BROKER_PORT}\n")
        f.write(f"Total unique topics: {len(topics)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, topic in enumerate(sorted(topics), 1):
            f.write(f"{i:3d}. {topic}\n")

def save_to_json(topics, filename):
    """Save topics to JSON file"""
    data = {
        'generated': datetime.now().isoformat(),
        'broker': f"{BROKER_HOST}:{BROKER_PORT}",
        'listen_duration_seconds': LISTEN_DURATION,
        'total_unique_topics': len(topics),
        'topics': sorted(list(topics))
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    global message_count
    
    print("🔍 MQTT Topic Discovery Tool")
    print(f"Broker: {BROKER_HOST}:{BROKER_PORT}")
    print(f"Listening for {LISTEN_DURATION} seconds...\n")
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Set username and password
        client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
        
        # Set TLS
        if USE_TLS:
            client.tls_set_context()
        
        # Connect to broker
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        
        # Start background network loop
        client.loop_start()
        
        # Listen for specified duration
        import time
        time.sleep(LISTEN_DURATION)
        
        # Stop loop
        client.loop_stop()
        client.disconnect()
        
    except ConnectionRefusedError:
        print(f"❌ Could not connect to {BROKER_HOST}:{BROKER_PORT}")
        print("Make sure the MQTT broker is running.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Save results
    print(f"\n✓ Listening complete!")
    print(f"  Received {message_count} messages")
    print(f"  Discovered {len(topics_set)} unique topics\n")
    
    if topics_set:
        print("Topics discovered:")
        for i, topic in enumerate(sorted(topics_set), 1):
            print(f"  {i:3d}. {topic}")
        
        # Save to files
        save_to_file(topics_set, OUTPUT_FILE)
        save_to_json(topics_set, OUTPUT_JSON)
        
        print(f"\n✓ Saved to: {OUTPUT_FILE}")
        print(f"✓ Saved to: {OUTPUT_JSON}")
    else:
        print("⚠ No messages received. Check broker connectivity.")
        sys.exit(1)

if __name__ == '__main__':
    main()
