#!/usr/bin/env python
"""
Script para probar la integración con DATADIS
Crea credenciales, autentica y sincroniza datos
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import DatadisCredentials, DatadisSupply, DatadisConsumption, DatadisMaxPower
from boreas_mediacion.datadis_service import DatadisService
from datetime import datetime, timedelta

def main():
    print("=" * 80)
    print("DATADIS Integration Test")
    print("=" * 80)
    
    # Paso 1: Crear/obtener credenciales
    print("\n1. Configurando credenciales...")
    credentials, created = DatadisCredentials.objects.get_or_create(
        username="B27441401",
        defaults={
            "password": "Jl.295469!",
            "active": True
        }
    )
    
    if created:
        print(f"   ✓ Credenciales creadas para usuario: {credentials.username}")
    else:
        print(f"   ✓ Usando credenciales existentes: {credentials.username}")
        # Actualizar contraseña por si acaso
        credentials.password = "Jl.295469!"
        credentials.active = True
        credentials.save()
    
    # Paso 2: Autenticar
    print("\n2. Autenticando con DATADIS...")
    try:
        service = DatadisService(credentials)
        token = service.authenticate()
        print(f"   ✓ Autenticación exitosa!")
        print(f"   Token: {token[:50]}..." if len(token) > 50 else f"   Token: {token}")
        print(f"   Expira: {credentials.token_expires_at}")
    except Exception as e:
        print(f"   ✗ Error en autenticación: {e}")
        return
    
    # Paso 3: Obtener puntos de suministro (CUPS)
    print("\n3. Sincronizando puntos de suministro (CUPS)...")
    try:
        created_count, updated_count = service.sync_supplies()
        print(f"   ✓ CUPS sincronizados: {created_count} nuevos, {updated_count} actualizados")
        
        # Mostrar CUPS
        supplies = DatadisSupply.objects.filter(credentials=credentials, active=True)
        print(f"\n   Puntos de suministro encontrados: {supplies.count()}")
        for supply in supplies:
            print(f"   - {supply.cups}")
            print(f"     Dirección: {supply.address}")
            print(f"     Provincia: {supply.province}, {supply.municipality}")
            print(f"     Distribuidor: {supply.distributor}")
            print()
    except Exception as e:
        print(f"   ✗ Error sincronizando CUPS: {e}")
        return
    
    # Paso 4: Sincronizar consumo (último mes)
    print("\n4. Sincronizando datos de consumo (último mes)...")
    if supplies.count() == 0:
        print("   ⚠ No hay CUPS para sincronizar")
        return
    
    # Tomar el primer CUPS como ejemplo
    supply = supplies.first()
    print(f"   Sincronizando CUPS: {supply.cups}")
    
    try:
        # Último mes - formato YYYY/MM
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Formatear fechas como YYYY/MM
        start_date_str = start_date.strftime('%Y/%m')
        end_date_str = end_date.strftime('%Y/%m')
        
        consumption_count = service.sync_consumption_data(
            supply=supply,
            start_date=start_date_str,
            end_date=end_date_str
        )
        print(f"   ✓ Registros de consumo sincronizados: {consumption_count}")
        
        # Mostrar algunos registros
        recent = DatadisConsumption.objects.filter(supply=supply).order_by('-date', '-time')[:5]
        if recent.exists():
            print(f"\n   Últimos registros de consumo:")
            for record in recent:
                print(f"   - {record.date} {record.time}: {record.consumption_kwh} kWh ({record.obtained_method})")
    except Exception as e:
        print(f"   ✗ Error sincronizando consumo: {e}")
        import traceback
        traceback.print_exc()
    
    # Paso 5: Sincronizar potencia máxima
    print("\n5. Sincronizando datos de potencia máxima...")
    try:
        max_power_count = service.sync_max_power(
            supply=supply,
            start_date=start_date_str,
            end_date=end_date_str
        )
        print(f"   ✓ Registros de potencia máxima sincronizados: {max_power_count}")
        
        # Mostrar algunos registros
        recent = DatadisMaxPower.objects.filter(supply=supply).order_by('-date', '-time')[:5]
        if recent.exists():
            print(f"\n   Últimos registros de potencia máxima:")
            for record in recent:
                print(f"   - {record.date} {record.time}: {record.max_power_kw} kW")
    except Exception as e:
        print(f"   ✗ Error sincronizando potencia: {e}")
        import traceback
        traceback.print_exc()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    total_supplies = DatadisSupply.objects.filter(credentials=credentials).count()
    total_consumption = DatadisConsumption.objects.count()
    total_max_power = DatadisMaxPower.objects.count()
    
    print(f"Total CUPS: {total_supplies}")
    print(f"Total registros de consumo: {total_consumption}")
    print(f"Total registros de potencia máxima: {total_max_power}")
    print(f"\nÚltima sincronización: {credentials.last_sync}")
    print("=" * 80)

if __name__ == "__main__":
    main()
