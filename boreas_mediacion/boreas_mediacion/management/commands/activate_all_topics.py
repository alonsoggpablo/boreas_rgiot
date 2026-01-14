from django.core.management.base import BaseCommand
from boreas_mediacion.models import MQTT_topic


class Command(BaseCommand):
    help = 'Activate all MQTT topics for reception from all families'

    def add_arguments(self, parser):
        parser.add_argument(
            '--family',
            type=str,
            help='Activate topics only for a specific family (optional)',
        )

    def handle(self, *args, **options):
        family_filter = options.get('family')
        
        if family_filter:
            # Activate topics for specific family
            count = MQTT_topic.objects.filter(family__name=family_filter).update(active=True)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Activated {count} topics for family "{family_filter}"')
            )
        else:
            # Activate all topics
            count = MQTT_topic.objects.all().update(active=True)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Activated {count} topics for all families')
            )
        
        # Display summary
        active_topics = MQTT_topic.objects.filter(active=True).count()
        total_topics = MQTT_topic.objects.count()
        self.stdout.write(f'Total active topics: {active_topics}/{total_topics}')
