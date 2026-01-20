"""
DATADIS API Service
Servicio para interactuar con la API de DATADIS (datos de consumo eléctrico)
"""
import requests
from datetime import datetime, timedelta, date
from django.utils import timezone
from .models import DatadisCredentials, DatadisSupply


class DatadisService:
    """Servicio para interactuar con la API de DATADIS"""
    
    BASE_URL = "https://datadis.es"
    AUTH_URL = f"{BASE_URL}/nikola-auth/tokens/login"
    API_BASE = f"{BASE_URL}/api-private/api"
    
    def __init__(self, credentials=None):
        """
        Inicializar servicio con credenciales
        
        Args:
            credentials: Objeto DatadisCredentials o None para usar las credenciales activas
        """
        if credentials is None:
            credentials = DatadisCredentials.objects.filter(active=True).first()
            if not credentials:
                raise ValueError("No se encontraron credenciales activas de DATADIS")
        
        self.credentials = credentials
        self.session = requests.Session()
    
    def authenticate(self):
        """
        Autenticar con DATADIS y obtener token
        
        Returns:
            str: Token de autenticación
        """
        url = f"{self.AUTH_URL}?username={self.credentials.username}&password={self.credentials.password}"
        
        try:
            response = self.session.post(url, timeout=120)
            response.raise_for_status()
            
            token = response.text.strip()
            
            # Guardar token y actualizar última autenticación
            self.credentials.auth_token = token
            self.credentials.last_auth = timezone.now()
            # Token expira en ~24 horas según la API
            self.credentials.token_expires_at = timezone.now() + timedelta(hours=23)
            self.credentials.save()
            
            return token
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error autenticando con DATADIS: {str(e)}")
    
    def get_token(self):
        """
        Obtener token válido (reutilizar existente o autenticar nuevamente)
        
        Returns:
            str: Token de autenticación válido
        """
        # Verificar si existe token y no ha expirado
        if self.credentials.auth_token and self.credentials.token_expires_at:
            if timezone.now() < self.credentials.token_expires_at:
                return self.credentials.auth_token
        
        # Token no existe o expiró, autenticar de nuevo
        return self.authenticate()
    
    def _make_request(self, endpoint, params=None):
        """
        Hacer petición a la API con manejo de autenticación
        
        Args:
            endpoint: Endpoint de la API (ej: 'get-supplies')
            params: Parámetros query string
        
        Returns:
            dict o list: Respuesta JSON de la API
        """
        token = self.get_token()
        url = f"{self.API_BASE}/{endpoint}"
        
        headers = {
            "Accept": "*/*",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=120)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token inválido, intentar reautenticar
                token = self.authenticate()
                headers["Authorization"] = f"Bearer {token}"
                response = self.session.get(url, headers=headers, params=params, timeout=120)
                response.raise_for_status()
                return response.json()
            raise
    
    def get_supplies(self, authorized_nif=None, distributor_code=None):
        """
        Obtener lista de puntos de suministro (CUPS)
        
        Args:
            authorized_nif (str, optional): NIF autorizado para buscar suministros
            distributor_code (str, optional): Código de distribuidora
        Returns:
            list: Lista de diccionarios con datos de suministros
        """
        params = {}
        if authorized_nif:
            params['authorizedNif'] = authorized_nif
        if distributor_code:
            params['distributorCode'] = distributor_code
        return self._make_request('get-supplies', params if params else None)
    
    def sync_supplies(self, authorized_nif=None, distributor_code=None):
        """
        Sincronizar puntos de suministro desde la API a la base de datos
        
        Args:
            authorized_nif (str, optional): NIF autorizado para buscar suministros
            distributor_code (str, optional): Código de distribuidora
        Returns:
            tuple: (creados, actualizados)
        """
        supplies_data = self.get_supplies(authorized_nif=authorized_nif, distributor_code=distributor_code)
        created_count = 0
        updated_count = 0
        
        for supply_data in supplies_data:
            cups = supply_data.get('cups')
            if not cups:
                continue
            
            # Convertir fechas
            valid_from = None
            valid_to = None
            if supply_data.get('validDateFrom'):
                try:
                    valid_from = datetime.strptime(supply_data['validDateFrom'], '%Y/%m/%d').date()
                except:
                    pass
            if supply_data.get('validDateTo'):
                try:
                    valid_to = datetime.strptime(supply_data['validDateTo'], '%Y/%m/%d').date()
                except:
                    pass
            
            # Crear o actualizar supply
            supply, created = DatadisSupply.objects.update_or_create(
                cups=cups,
                defaults={
                    'credentials': self.credentials,
                    'address': supply_data.get('address', ''),
                    'postal_code': supply_data.get('postalCode', ''),
                    'province': supply_data.get('province', ''),
                    'municipality': supply_data.get('municipality', ''),
                    'distributor': supply_data.get('distributor', ''),
                    'distributor_code': supply_data.get('distributorCode', ''),
                    'point_type': supply_data.get('pointType'),
                    'valid_date_from': valid_from,
                    'valid_date_to': valid_to,
                    'raw_data': supply_data
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.credentials.last_sync = timezone.now()
        self.credentials.save()
        
        return created_count, updated_count
    
    
    def sync_all_supplies_consumption(self, start_date=None, end_date=None):
        """
        Sincronizar consumo para todos los supplies activos
        
        Args:
            start_date: Fecha inicio (YYYY/MM)
            end_date: Fecha fin (YYYY/MM)
        
        Returns:
            dict: Resumen de la sincronización
        """
        supplies = DatadisSupply.objects.filter(
            credentials=self.credentials,
            active=True
        )
        
        results = {
            'total_supplies': supplies.count(),
            'processed': 0,
            'consumption_records': 0,
            'max_power_records': 0,
            'errors': []
        }
        
        for supply in supplies:
            try:
                # Sincronizar consumo
                consumption_count = self.sync_consumption_data(supply, start_date, end_date)
                results['consumption_records'] += consumption_count
                
                # Sincronizar potencia máxima
                power_count = self.sync_max_power(supply, start_date, end_date)
                results['max_power_records'] += power_count
                
                results['processed'] += 1
            
            except Exception as e:
                results['errors'].append({
                    'cups': supply.cups,
                    'error': str(e)
                })
        
        return results
