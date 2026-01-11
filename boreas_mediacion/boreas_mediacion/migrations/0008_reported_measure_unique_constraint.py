# Generated migration to add unique_together constraint on reported_measure

from django.db import migrations, models


def delete_old_measures(apps, schema_editor):
    """Keep only the latest measure for each feed+device_id combination"""
    ReportedMeasure = apps.get_model('boreas_mediacion', 'reported_measure')
    
    from django.db.models import Max
    
    # Get the latest measure ID for each feed+device_id
    latest_measures = list(
        ReportedMeasure.objects
        .values('feed', 'device_id')
        .annotate(latest_id=Max('id'))
        .values_list('latest_id', flat=True)
    )
    
    # Delete all measures that are not the latest for their feed+device_id
    deleted_count, _ = ReportedMeasure.objects.exclude(id__in=latest_measures).delete()
    
    if deleted_count > 0:
        print(f"\n✅ Deleted {deleted_count} old reported_measure records, kept only the latest for each device\n")


class Migration(migrations.Migration):

    dependencies = [
        ('boreas_mediacion', '0007_alert_alertrule_alertnotification_alert_rule'),
    ]

    operations = [
        # First delete the old duplicates via raw SQL to ensure it happens
        migrations.RunSQL(
            sql="""
            DELETE FROM boreas_mediacion_reported_measure 
            WHERE id NOT IN (
                SELECT MAX(id) 
                FROM boreas_mediacion_reported_measure 
                GROUP BY feed, device_id
            );
            """,
            reverse_sql="-- Cannot reverse data deletion",
        ),
        # Then add the unique constraint
        migrations.AlterUniqueTogether(
            name='reported_measure',
            unique_together={('feed', 'device_id')},
        ),
    ]
