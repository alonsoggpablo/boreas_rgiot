from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("boreas_mediacion", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reported_measure",
            name="report_time",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="reported_measure",
            name="device_id",
            field=models.CharField(max_length=100, default="unknown", db_index=True),
        ),
        migrations.AlterField(
            model_name="reported_measure",
            name="feed",
            field=models.CharField(max_length=100, default="unknown", db_index=True),
        ),
        migrations.AlterUniqueTogether(
            name="reported_measure",
            unique_together=set(),
        ),
        migrations.AddIndex(
            model_name="reported_measure",
            index=models.Index(
                fields=["device_id", "feed", "report_time"],
                name="reported_measure_device_feed_time_idx",
            ),
        ),
    ]
