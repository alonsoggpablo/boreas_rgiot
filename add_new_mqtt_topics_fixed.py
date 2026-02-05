#!/usr/bin/env python
"""
Add discovered MQTT topics to database with proper broker and family mapping
"""
import os
import django
import json
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
sys.path.insert(0, '/app/boreas_mediacion')
django.setup()

from boreas_mediacion.models import MQTT_topic, MQTT_broker, MQTT_device_family

def get_family_for_topic(topic):
    """Determine family based on topic prefix"""
    topic_lower = topic.lower()
    
    # Map topic prefixes to family names
    family_mappings = {
        'gadget': 'gadget',
        'shellies': 'shellies',
        'prueba': 'gadget',  # Default unknown topics to gadget
        'iaq': 'IAQ_Measures',
        'aemet': 'aemet',
        'sig': 'sigfox',
        'datadis': 'datadis',
    }
    
    # Check each prefix
    for prefix, family_name in family_mappings.items():
        if topic_lower.startswith(prefix):
            try:
                return MQTT_device_family.objects.get(name=family_name)
            except MQTT_device_family.DoesNotExist:
                pass
    
    # Default to "gadget" family or get first family
    try:
        return MQTT_device_family.objects.get(name='gadget')
    except MQTT_device_family.DoesNotExist:
        # Use first available family
        return MQTT_device_family.objects.first()

def load_comparison_data():
    """Load the comparison JSON file"""
    comparison_file = '/app/mqtt_topics_comparison.json'
    try:
        with open(comparison_file, 'r') as f:
            data = json.load(f)
        return data.get('details', {}).get('only_in_broker', [])
    except FileNotFoundError:
        print(f"❌ Comparison file not found: {comparison_file}")
        return []

def add_topics_to_db(topics):
    """Add topics to database"""
    # Get the rgiot broker (ID: 1)
    try:
        broker = MQTT_broker.objects.get(id=1)
    except MQTT_broker.DoesNotExist:
        print("❌ Default broker (ID: 1) not found!")
        return
    
    print(f"\n📊 Processing {len(topics)} new topics...")
    print(f"   Using broker: {broker.name} ({broker.server}:{broker.port})")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    errors = []
    
    for topic in topics:
        try:
            # Check if topic already exists
            if MQTT_topic.objects.filter(topic=topic).exists():
                skipped_count += 1
                continue
            
            # Determine family
            family = get_family_for_topic(topic)
            
            # Create the MQTT topic
            mqtt_topic = MQTT_topic.objects.create(
                broker=broker,
                family=family,
                topic=topic,
                qos=0,
                description='',
                active=True,
                ro_rw='ro'
            )
            created_count += 1
            
        except Exception as e:
            error_count += 1
            errors.append({
                'topic': topic,
                'error': str(e)
            })
    
    # Report results
    print(f"\n{'='*70}")
    print(f"✓ COMPLETED")
    print(f"{'='*70}")
    print(f"  Created:  {created_count} new topics")
    print(f"  Skipped:  {skipped_count} (already existed)")
    print(f"  Errors:   {error_count}")
    
    if errors:
        print(f"\n❌ Errors (showing first 5):")
        for err in errors[:5]:
            print(f"  - {err['topic']}: {err['error']}")
        if error_count > 5:
            print(f"  ... and {error_count - 5} more errors")
    
    print(f"\n✓ Total topics in database: {MQTT_topic.objects.count()}")

if __name__ == '__main__':
    # Load topics from comparison file
    new_topics = load_comparison_data()
    
    if not new_topics:
        print("❌ No new topics to add")
        sys.exit(1)
    
    print(f"Loaded {len(new_topics)} new topics from comparison report")
    
    # Show preview
    print(f"\n📋 Preview of topics to add (first 10):")
    for i, topic in enumerate(new_topics[:10], 1):
        family = get_family_for_topic(topic)
        print(f"   {i:3d}. {topic:<50} → Family: {family.name}")
    
    if len(new_topics) > 10:
        print(f"   ... and {len(new_topics) - 10} more topics")
    
    # Confirm
    confirm = input(f"\nAdd {len(new_topics)} topics to database? (yes/no): ").lower().strip()
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled")
        sys.exit(0)
    
    # Add topics
    add_topics_to_db(new_topics)
