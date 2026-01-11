"""
Management command para sincronizar datos de WirelessLogic SIMPro API
"""
from django.core.management.base import BaseCommand
from boreas_mediacion.wirelesslogic_service import WirelessLogicService


class Command(BaseCommand):
    help = 'Sincroniza datos de SIMs y uso desde WirelessLogic SIMPro API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='Número de días hacia atrás para sincronizar datos de uso (default: 30)'
        )
        parser.add_argument(
            '--sims-only',
            action='store_true',
            help='Sincronizar solo información de SIMs, no datos de uso'
        )
        parser.add_argument(
            '--usage-only',
            action='store_true',
            help='Sincronizar solo datos de uso, no información de SIMs'
        )

    def handle(self, *args, **options):
        days_back = options['days_back']
        sims_only = options['sims_only']
        usage_only = options['usage_only']
        
        service = WirelessLogicService()
        
        # Sincronizar SIMs
        if not usage_only:
            self.stdout.write(self.style.NOTICE('Sincronizando información de SIMs...'))
            try:
                created, updated = service.sync_all_sims()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ SIMs sincronizadas: {created} creadas, {updated} actualizadas'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error sincronizando SIMs: {str(e)}')
                )
                return
        
        # Sincronizar datos de uso
        if not sims_only:
            self.stdout.write(
                self.style.NOTICE(f'Sincronizando datos de uso (últimos {days_back} días)...')
            )
            try:
                usage_count = service.sync_sim_usage(days_back=days_back)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Registros de uso sincronizados: {usage_count}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error sincronizando uso: {str(e)}')
                )
                return
        
        self.stdout.write(self.style.SUCCESS('\n✓ Sincronización completada exitosamente'))
