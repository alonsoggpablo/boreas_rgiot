#!/usr/bin/env python
"""
Script para añadir topics y feeds MQTT necesarios para:
- Teltonika routers (router/+/#  y rgiot/devices/router)
- Datos meteorológicos AEMET (si no existen)
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boreas_mediacion.settings")
django.setup()

from boreas_mediacion.models import MQTT_topic, MQTT_feed, MQTT_broker, MQTT_device_family

def get_or_create_broker():
    """Obtiene el broker principal o lo crea si no existe"""
    broker = MQTT_broker.objects.first()
    if not broker:
        broker = MQTT_broker.objects.create(
            name="MQTT Broker Principal",
            host="mqtt.solutions-iot.es",
            port=8883,
            username="rgiot",
            password="rg2020iot",
            use_tls=True,
            protocol_version=4
        )
        print(f"✓ Broker creado: {broker.name}")
    else:
        print(f"✓ Broker encontrado: {broker.name}")
    return broker

def get_or_create_device_family(family_name):
    """Obtiene o crea una familia de dispositivos"""
    family, created = MQTT_device_family.objects.get_or_create(name=family_name)
    if created:
        print(f"  + Familia creada: {family_name}")
    return family

def create_topic_and_feed(topic_str, feed_name, description, broker, family_name):
    """Crea un topic y su feed asociado si no existen"""
    
    # Verificar si el feed ya existe
    existing_feed = MQTT_feed.objects.filter(name=feed_name).first()
    if existing_feed:
        print(f"  ⚠ Feed ya existe: {feed_name}")
        return existing_feed
    
    # Obtener o crear la familia
    family = get_or_create_device_family(family_name)
    
    # Crear el topic
    topic, created = MQTT_topic.objects.get_or_create(
        topic=topic_str,
        defaults={'qos': 0, 'broker': broker, 'family': family}
    )
    
    if created:
        print(f"  + Topic creado: {topic_str}")
    else:
        print(f"  ⚠ Topic ya existía: {topic_str}")
    
    # Crear el feed
    feed = MQTT_feed.objects.create(
        name=feed_name,
        description=description,
        topic=topic
    )
    print(f"  ✓ Feed creado: {feed_name}")
    
    return feed

def main():
    print("\n" + "="*80)
    print(" CONFIGURACIÓN DE TOPICS Y FEEDS MQTT")
    print("="*80 + "\n")
    
    # Obtener o crear broker
    broker = get_or_create_broker()
    
    # Lista de topics y feeds a crear
    topics_to_create = [
        {
            'topic': 'router/+/#',
            'feed_name': 'router',
            'description': 'Feed para mensajes de routers Teltonika (entrada)',
            'family': 'router'
        },
        {
            'topic': 'rgiot/devices/router',
            'feed_name': 'rgiot/devices/router',
            'description': 'Feed para datos procesados de routers Teltonika (salida)',
            'family': 'rgiot'
        },
        {
            'topic': 'aemet/estaciones',
            'feed_name': 'aemet/estaciones',
            'description': 'Feed para datos meteorológicos de estaciones AEMET',
            'family': 'aemet'
        },
    ]
    
    print("\n📋 Creando topics y feeds:\n")
    
    for item in topics_to_create:
        print(f"🔧 Procesando: {item['feed_name']}")
        create_topic_and_feed(
            topic_str=item['topic'],
            feed_name=item['feed_name'],
            description=item['description'],
            broker=broker,
            family_name=item['family']
        )
        print()
    
    # Mostrar resumen
    print("="*80)
    print(" RESUMEN")
    print("="*80)
    
    total_topics = MQTT_topic.objects.count()
    total_feeds = MQTT_feed.objects.count()
    
    print(f"\n📊 Total de topics en la base de datos: {total_topics}")
    print(f"📊 Total de feeds en la base de datos: {total_feeds}")
    
    # Mostrar los feeds recién creados/verificados
    print("\n📍 Feeds de Teltonika y AEMET:")
    for item in topics_to_create:
        feed = MQTT_feed.objects.filter(name=item['feed_name']).first()
        if feed:
            print(f"  ✓ {feed.name} → {feed.topic.topic}")
        else:
            print(f"  ✗ {item['feed_name']} NO ENCONTRADO")
    
    print("\n" + "="*80)
    print(" ✅ CONFIGURACIÓN COMPLETADA")
    print("="*80 + "\n")
    
    print("📝 Siguiente paso:")
    print("   1. Iniciar el cliente MQTT desde el admin de Django")
    print("   2. El broker se suscribirá a:")
    print("      - router/+/# (Teltonika)")
    print("      - IAQ_Measures/tactica (ya existente)")
    print("      - aemet/estaciones")
    print("\n")

if __name__ == "__main__":
    main()
