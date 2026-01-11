"""
Django management command to check for new AEMET weather data arrivals
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from boreas_mediacion.models import reported_measure


class Command(BaseCommand):
    help = 'Check for new AEMET weather data and send email notification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=5,
            help='Check for AEMET data received in the last N minutes (default: 5)',
        )
        parser.add_argument(
            '--recipient',
            type=str,
            default='alonsogpablo@gestionyenergia.com',
            help='Email recipient',
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        recipient = options['recipient']
        
        # Calculate time threshold
        time_threshold = timezone.now() - timedelta(minutes=minutes)
        
        # Query for recent AEMET data
        recent_aemet = reported_measure.objects.filter(
            feed__iexact='aemet',
            report_time__gte=time_threshold
        ).order_by('-report_time')
        
        count = recent_aemet.count()
        
        if count > 0:
            # Prepare email content
            subject = f'🌤️ AEMET Data Arrival Notification'
            
            # Build message with details
            message_lines = [
                f'New AEMET weather data detected!',
                f'',
                f'Total records received in last {minutes} minutes: {count}',
                f'Check time: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}',
                f'',
                f'Recent stations:',
            ]
            
            # Add details of up to 10 most recent records
            for record in recent_aemet[:10]:
                station_id = record.device_id
                report_time = record.report_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Extract some key measures if available
                measures = record.measures
                temp_info = ''
                if isinstance(measures, dict):
                    if 'ta' in measures:
                        temp_info = f" - Temp: {measures['ta']}°C"
                    elif 'temperature' in measures:
                        temp_info = f" - Temp: {measures['temperature']}°C"
                
                message_lines.append(f'  - Station {station_id} at {report_time}{temp_info}')
            
            if count > 10:
                message_lines.append(f'  ... and {count - 10} more records')
            
            message = '\n'.join(message_lines)
            
            # Send email
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Email sent to {recipient} - {count} AEMET records found'
                    )
                )
                
                # Also print to stdout for Airflow logs
                self.stdout.write(f'\n{message}\n')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to send email: {str(e)}')
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'ℹ️  No new AEMET data in the last {minutes} minutes'
                )
            )
