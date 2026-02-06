"""
Dump reported_measure records older than 7 days to Parquet files.
Keeps rolling 7-day window in PostgreSQL, archives older data to Parquet.
"""
import os
import sys
import django
from datetime import datetime, timedelta
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
sys.path.insert(0, '/app')
django.setup()

from boreas_mediacion.models import reported_measure
from django.db.models import Q

# Configuration
PARQUET_DIR = '/app/data/reported_measures_archive'
RETENTION_DAYS = 7

def ensure_parquet_dir():
    """Create parquet directory if it doesn't exist."""
    os.makedirs(PARQUET_DIR, exist_ok=True)
    print(f"✓ Parquet directory: {PARQUET_DIR}")

def dump_date_range(start_date, end_date):
    """
    Dump reported_measure records for a specific date range to Parquet.
    
    Args:
        start_date: datetime - start of range (inclusive)
        end_date: datetime - end of range (exclusive)
    
    Returns:
        bool - True if successful, False otherwise
    """
    try:
        # Query records for this date range
        queryset = reported_measure.objects.filter(
            report_time__gte=start_date,
            report_time__lt=end_date
        ).order_by('report_time')
        
        count = queryset.count()
        if count == 0:
            print(f"  No records for {start_date.date()}")
            return False
        
        # Convert to DataFrame
        data = []
        for rm in queryset:
            data.append({
                'id': rm.id,
                'report_time': rm.report_time,
                'device_id': rm.device_id,
                'device': rm.device,
                'measures': rm.measures,
                'feed': rm.feed,
                'device_family_id': rm.device_family_id,
                'nanoenvi_uuid': rm.nanoenvi_uuid,
                'nanoenvi_name': rm.nanoenvi_name,
                'nanoenvi_client': rm.nanoenvi_client,
            })
        
        df = pd.DataFrame(data)
        
        # Define Parquet path
        filename = f"reported_measures_{start_date.date()}.parquet"
        filepath = os.path.join(PARQUET_DIR, filename)
        
        # Write to Parquet
        df.to_parquet(filepath, index=False, compression='snappy')
        
        print(f"  ✓ {filename}: {count} records ({df.memory_usage(deep=True).sum() / 1024:.1f} KB)")
        return True
        
    except Exception as e:
        print(f"  ✗ Error dumping {start_date.date()}: {e}")
        return False

def cleanup_old_records(retention_days):
    """
    Delete records older than retention_days from PostgreSQL.
    Only deletes after successful Parquet dump.
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    count, _ = reported_measure.objects.filter(
        report_time__lt=cutoff_date
    ).delete()
    
    if count > 0:
        print(f"✓ Deleted {count} records older than {retention_days} days")
    return count

def dump_to_parquet():
    """Main function: dump all records older than RETENTION_DAYS to Parquet."""
    print(f"\n{'='*60}")
    print(f"Dumping reported_measures to Parquet (retention: {RETENTION_DAYS} days)")
    print(f"{'='*60}")
    
    ensure_parquet_dir()
    
    # Calculate date range to dump: everything older than retention window
    now = datetime.now()
    cutoff_date = now - timedelta(days=RETENTION_DAYS)
    
    # Get earliest record
    earliest = reported_measure.objects.order_by('report_time').first()
    if not earliest:
        print("No records to dump.")
        return
    
    print(f"Date range: {earliest.report_time.date()} to {cutoff_date.date()}")
    print(f"Dumping in daily chunks...\n")
    
    # Dump each day as separate Parquet file
    current_date = earliest.report_time.date()
    dumped_count = 0
    
    while current_date < cutoff_date.date():
        start = datetime.combine(current_date, datetime.min.time())
        end = start + timedelta(days=1)
        
        if dump_date_range(start, end):
            dumped_count += 1
        
        current_date += timedelta(days=1)
    
    print(f"\n✓ Dumped {dumped_count} days to Parquet")
    
    # Clean up old records from PostgreSQL
    print("\nCleaning up old records from PostgreSQL...")
    deleted = cleanup_old_records(RETENTION_DAYS)
    
    print(f"\n{'='*60}")
    print(f"Done! Kept {RETENTION_DAYS} days in PostgreSQL, archived rest to Parquet.")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    dump_to_parquet()
