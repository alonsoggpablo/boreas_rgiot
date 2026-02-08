"""
Dump reported_measure records to Parquet files before TimescaleDB retention policy deletes them.
TimescaleDB retention policy: 24 hours
This script dumps data between 20-23 hours old to ensure archival before auto-deletion.
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
from django.utils import timezone

# Configuration
PARQUET_DIR = '/app/data/reported_measures_archive'
RETENTION_HOURS = 24
ARCHIVE_START_HOURS = 23  # Start archiving at 23 hours old
ARCHIVE_END_HOURS = 20    # Archive up to 20 hours old

def _ensure_aware(dt):
    """Ensure datetime is timezone-aware using current timezone."""
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

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

def cleanup_old_records(cutoff_date):
    """
    NOTE: Deletion is handled by TimescaleDB retention policy (24 hours).
    This function is kept for compatibility but does nothing.
    Django model is managed=False, so Django should not delete from hypertable.
    """
    print(f"ℹ Skipping manual deletion - TimescaleDB retention policy handles this automatically")
    return 0

def dump_to_parquet():
    """Main function: dump data between 20-23 hours old before TimescaleDB retention deletes it."""
    print(f"\n{'='*60}")
    print(f"Dumping reported_measures to Parquet")
    print(f"Archive window: {ARCHIVE_END_HOURS}-{ARCHIVE_START_HOURS} hours old")
    print(f"TimescaleDB retention: {RETENTION_HOURS} hours")
    print(f"{'='*60}")
    
    ensure_parquet_dir()
    
    # Calculate date range to dump: data between ARCHIVE_END_HOURS and ARCHIVE_START_HOURS old
    now = timezone.now()
    archive_start = now - timedelta(hours=ARCHIVE_START_HOURS)
    archive_end = now - timedelta(hours=ARCHIVE_END_HOURS)
    
    # Query records in the archive window
    queryset = reported_measure.objects.filter(
        report_time__gte=archive_start,
        report_time__lt=archive_end
    ).order_by('report_time')
    
    count = queryset.count()
    if count == 0:
        print(f"No records in archive window ({archive_start} to {archive_end})")
        return
    
    print(f"Date range: {archive_start} to {archive_end}")
    print(f"Records to archive: {count}\n")
    
    # Dump each day as separate Parquet file
    current_date = archive_start.date()
    dumped_count = 0
    
    while current_date <= archive_end.date():
        start = _ensure_aware(datetime.combine(current_date, datetime.min.time()))
        end = min(start + timedelta(days=1), archive_end)
        
        # Ensure we don't go beyond archive window
        if start >= archive_end:
            break
            
        if dump_date_range(max(start, archive_start), end):
            dumped_count += 1
        
        current_date += timedelta(days=1)

    print(f"\n✓ Dumped {dumped_count} file(s) to Parquet")
    
    # Note about cleanup
    print(f"\nℹ Records older than {RETENTION_HOURS}h will be auto-deleted by TimescaleDB retention policy")
    
    print(f"\n{'='*60}")
    print(f"Done! Archived {count} records to Parquet. TimescaleDB manages retention.")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    dump_to_parquet()
