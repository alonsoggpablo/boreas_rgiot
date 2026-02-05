#!/usr/bin/env python3
"""
Compare MQTT topics discovered from broker vs topics in database.
"""

import os
import sys
import django
import json

# Add Django to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boreas_mediacion'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import MQTT_topic

def load_discovered_topics(filename='mqtt_topics_discovered.txt'):
    """Load topics from discovered file"""
    topics = set()
    with open(filename, 'r') as f:
        lines = f.readlines()
        # Skip header lines until we see the separator
        in_topics = False
        for line in lines:
            if '===' in line:
                in_topics = True
                continue
            if in_topics and line.strip():
                # Extract topic from "  N. topic_name"
                parts = line.strip().split('. ', 1)
                if len(parts) > 1:
                    topics.add(parts[1])
    return topics

def get_database_topics():
    """Get all topics from database"""
    topics = set()
    db_topics = MQTT_topic.objects.all().values_list('topic', flat=True)
    for topic in db_topics:
        topics.add(topic)
    return topics

def compare_topics(discovered, database):
    """Compare topic sets"""
    only_in_broker = discovered - database
    only_in_db = database - discovered
    in_both = discovered & database
    
    return {
        'only_in_broker': sorted(only_in_broker),
        'only_in_database': sorted(only_in_db),
        'in_both': sorted(in_both),
    }

def main():
    print("📊 MQTT Topics Comparison\n")
    
    # Load discovered topics
    print("Loading discovered topics from file...")
    discovered = load_discovered_topics()
    print(f"✓ Found {len(discovered)} topics in broker\n")
    
    # Get database topics
    print("Loading topics from database...")
    database = get_database_topics()
    print(f"✓ Found {len(database)} topics in database\n")
    
    # Compare
    print("Comparing...\n")
    comparison = compare_topics(discovered, database)
    
    # Results
    print("=" * 70)
    print(f"✓ MATCHED TOPICS: {len(comparison['in_both'])}")
    print("=" * 70)
    
    print(f"\n⚠️  ONLY IN BROKER ({len(comparison['only_in_broker'])} topics):")
    print("-" * 70)
    if comparison['only_in_broker']:
        for i, topic in enumerate(comparison['only_in_broker'][:20], 1):
            print(f"  {i:3d}. {topic}")
        if len(comparison['only_in_broker']) > 20:
            print(f"  ... and {len(comparison['only_in_broker']) - 20} more")
    else:
        print("  (None)")
    
    print(f"\n🚫 ONLY IN DATABASE ({len(comparison['only_in_database'])} topics):")
    print("-" * 70)
    if comparison['only_in_database']:
        for i, topic in enumerate(comparison['only_in_database'][:20], 1):
            print(f"  {i:3d}. {topic}")
        if len(comparison['only_in_database']) > 20:
            print(f"  ... and {len(comparison['only_in_database']) - 20} more")
    else:
        print("  (None)")
    
    # Save detailed report
    report = {
        'summary': {
            'total_in_broker': len(discovered),
            'total_in_database': len(database),
            'matched': len(comparison['in_both']),
            'only_in_broker': len(comparison['only_in_broker']),
            'only_in_database': len(comparison['only_in_database']),
        },
        'details': comparison
    }
    
    with open('mqtt_topics_comparison.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Detailed report saved to: mqtt_topics_comparison.json")
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"  Total broker topics:    {len(discovered)}")
    print(f"  Total database topics:  {len(database)}")
    print(f"  Matched:                {len(comparison['in_both'])} ({100*len(comparison['in_both'])//len(discovered)}%)")
    print(f"  Missing in DB:          {len(comparison['only_in_broker'])}")
    print(f"  Obsolete in DB:         {len(comparison['only_in_database'])}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
