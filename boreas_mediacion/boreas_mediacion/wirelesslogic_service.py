"""
Servicio para interactuar con la API de WirelessLogic SIMPro
"""
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import WirelessLogic_SIM, WirelessLogic_Usage


class WirelessLogicAPIError(Exception):
    """Excepción personalizada para errores de API WirelessLogic"""
    pass


class WirelessLogicService:
    """Servicio para consultar y sincronizar datos de SIMs desde WirelessLogic API"""
    
    BASE_URL = "https://simpro4.wirelesslogic.com/api/v3"
    
    def __init__(self):
        # Credenciales de la API (deberían estar en settings.py o variables de entorno)
        self.api_client = getattr(settings, 'WIRELESSLOGIC_API_CLIENT', 
                                  '476eaa4582823d0c2eb2b13a7dee2abdc8c501e52b6f0d27deb9a824f0b2d7d0-033430-1791068399')
        self.api_key = getattr(settings, 'WIRELESSLOGIC_API_KEY',
                               '509993e98871319ccb6a61a77f2f097bae1c4af69e2e3274bc49a782d534c6f9')
        
        self.headers = {
            'x-api-client': self.api_client,
            'x-api-key': self.api_key,
            'Accept': 'application/json'
        }
    
    def _make_request(self, endpoint, params=None):
        """Realiza una petición GET a la API de WirelessLogic"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise WirelessLogicAPIError(f"Error al consultar API WirelessLogic: {str(e)}")
    
    def get_all_sims(self):
        """Obtiene la lista de todas las SIMs"""
        try:
            data = self._make_request('sims')
            return data.get('sims', [])
        except Exception as e:
            print(f"Error obteniendo SIMs: {e}")
            return []
    
    def get_sim_details(self, iccids):
        """
        Obtiene detalles de SIMs específicas
        
        Args:
            iccids: Lista de ICCIDs o string separado por comas
        
        Returns:
            Lista de detalles de SIMs
        """
        if isinstance(iccids, list):
            iccids = ','.join(iccids)
        
        try:
            params = {
                'identifierType': 'iccid',
                'identifiers': iccids
            }
            return self._make_request('sims/details', params=params)
        except Exception as e:
            print(f"Error obteniendo detalles de SIM: {e}")
            return []
    
    def get_usage_data(self, iccids, start_date=None, end_date=None):
        """
        Obtiene datos de uso de SIMs
        
        Args:
            iccids: Lista de ICCIDs o string separado por comas
            start_date: Fecha inicio (datetime o string ISO)
            end_date: Fecha fin (datetime o string ISO)
        
        Returns:
            Datos de uso
        """
        if isinstance(iccids, list):
            iccids = ','.join(iccids)
        
        params = {'identifiers': iccids}
        
        if start_date:
            if isinstance(start_date, datetime):
                start_date = start_date.isoformat()
            params['startDate'] = start_date
        
        if end_date:
            if isinstance(end_date, datetime):
                end_date = end_date.isoformat()
            params['endDate'] = end_date
        
        try:
            data = self._make_request('sims/usage', params=params)
            return data.get('sims', [])
        except Exception as e:
            print(f"Error obteniendo datos de uso: {e}")
            return []
    
    def sync_all_sims(self):
        """
        Sincroniza todas las SIMs desde la API al modelo Django
        
        Returns:
            Tuple (sims_creadas, sims_actualizadas)
        """
        created_count = 0
        updated_count = 0
        
        # Obtener lista de SIMs
        sims_list = self.get_all_sims()
        
        if not sims_list:
            print("No se obtuvieron SIMs de la API")
            return 0, 0
        
        # Extraer ICCIDs
        iccids = [sim.get('iccid') for sim in sims_list if sim.get('iccid')]
        
        if not iccids:
            print("No se encontraron ICCIDs válidos")
            return 0, 0
        
        # Obtener detalles de todas las SIMs (en lotes de 100)
        batch_size = 100
        for i in range(0, len(iccids), batch_size):
            batch_iccids = iccids[i:i + batch_size]
            sim_details = self.get_sim_details(batch_iccids)
            
            for sim_data in sim_details:
                created, updated = self._save_sim_to_db(sim_data)
                if created:
                    created_count += 1
                elif updated:
                    updated_count += 1
        
        return created_count, updated_count
    
    def sync_sim_usage(self, days_back=30):
        """
        Sincroniza datos de uso de todas las SIMs
        
        Args:
            days_back: Número de días hacia atrás para obtener uso
        
        Returns:
            Número de registros de uso creados
        """
        usage_count = 0
        
        # Obtener todas las SIMs de la BD
        sims = WirelessLogic_SIM.objects.all()
        iccids = list(sims.values_list('iccid', flat=True))
        
        if not iccids:
            print("No hay SIMs en la base de datos para sincronizar uso")
            return 0
        
        # Calcular rango de fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Obtener datos de uso en lotes
        batch_size = 100
        for i in range(0, len(iccids), batch_size):
            batch_iccids = iccids[i:i + batch_size]
            usage_data = self.get_usage_data(batch_iccids, start_date, end_date)
            
            for usage_record in usage_data:
                count = self._save_usage_to_db(usage_record)
                usage_count += count
        
        return usage_count
    
    def _save_sim_to_db(self, sim_data):
        """
        Guarda o actualiza una SIM en la base de datos
        
        Returns:
            Tuple (created, updated)
        """
        iccid = sim_data.get('iccid')
        
        if not iccid:
            return False, False
        
        # Extraer datos de la conexión activa
        active_conn = sim_data.get('active_connection', {}) or {}
        
        # Extraer campos relevantes
        sim_fields = {
            'iccid': iccid,
            'msisdn': active_conn.get('msisdn') or active_conn.get('local'),
            'imsi': active_conn.get('imsi'),
            'status': active_conn.get('customer_status', {}).get('ident') if active_conn.get('customer_status') else None,
            'tariff_name': active_conn.get('customer_tariff', {}).get('name') if active_conn.get('customer_tariff') else None,
            'account_name': sim_data.get('billing_account', {}).get('name') if sim_data.get('billing_account') else None,
            'network': sim_data.get('mno_account', {}).get('mno', {}).get('name') if sim_data.get('mno_account') else None,
            'roaming_network': None,  # No disponible en esta estructura
            'raw_data': sim_data
        }
        
        # Parsear fecha de activación si existe
        activation_date_str = active_conn.get('activation_date')
        if activation_date_str:
            try:
                # Formato: "2025-02-26"
                from datetime import datetime
                sim_fields['activation_date'] = datetime.strptime(activation_date_str, '%Y-%m-%d')
            except:
                pass
        
        # Crear o actualizar
        sim, created = WirelessLogic_SIM.objects.update_or_create(
            iccid=iccid,
            defaults=sim_fields
        )
        
        return created, not created
    
    def _save_usage_to_db(self, usage_data):
        """
        Guarda datos de uso en la base de datos
        
        La API devuelve datos "month-to-date" (acumulados del mes actual)
        con los campos:
        - month_to_date_bytes_up/down
        - month_to_date_voice_up/down  
        - month_to_date_sms_up/down
        - last_seen
        
        Returns:
            Número de registros creados/actualizados
        """
        iccid = usage_data.get('iccid')
        
        if not iccid:
            return 0
        
        try:
            sim = WirelessLogic_SIM.objects.get(iccid=iccid)
        except WirelessLogic_SIM.DoesNotExist:
            print(f"SIM {iccid} no encontrada en BD")
            return 0
        
        # Los datos son month-to-date, así que el período es el mes actual
        now = timezone.now()
        # Período: inicio del mes actual hasta ahora
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = now
        
        # Extraer datos de uso (convertir bytes a MB)
        bytes_up = int(usage_data.get('month_to_date_bytes_up', 0))
        bytes_down = int(usage_data.get('month_to_date_bytes_down', 0))
        total_bytes = bytes_up + bytes_down
        data_mb = round(total_bytes / (1024 * 1024), 2)  # Convertir a MB
        
        # SMS (envío + recepción)
        sms_sent = int(usage_data.get('month_to_date_sms_up', 0))
        sms_received = int(usage_data.get('month_to_date_sms_down', 0))
        
        # Voz (en segundos, convertir a minutos)
        voice_up = int(usage_data.get('month_to_date_voice_up', 0))
        voice_down = int(usage_data.get('month_to_date_voice_down', 0))
        total_voice_seconds = voice_up + voice_down
        voice_mins = round(total_voice_seconds / 60, 2)
        
        # Crear o actualizar registro de uso
        usage, created = WirelessLogic_Usage.objects.update_or_create(
            sim=sim,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'data_used_mb': data_mb,
                'sms_sent': sms_sent,
                'sms_received': sms_received,
                'voice_minutes': voice_mins,
                'raw_data': usage_data
            }
        )
        
        return 1 if created else 0
