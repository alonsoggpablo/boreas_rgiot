# Fixtures - Datos Iniciales para Despliegue

Este directorio contiene los datos básicos necesarios para inicializar la base de datos en un nuevo despliegue del sistema Boreas RGIOT.

## Archivos de Fixtures

Los archivos están numerados en el orden en que deben cargarse para respetar las dependencias entre modelos:

1. **01_mqtt_device_families.json** - Familias de dispositivos MQTT (aemet, shellies, etc.)
2. **02_mqtt_brokers.json** - Configuración de brokers MQTT
3. **03_mqtt_topics.json** - Topics MQTT configurados (depende de brokers y familias)
4. **04_sensor_actuaciones.json** - Tipos de actuaciones disponibles para sensores
5. **05_router_parameters.json** - Parámetros de configuración de routers

## Cómo Cargar los Fixtures

### En desarrollo local (con manage.py)

```bash
# Cargar todos los fixtures en orden
python manage.py loaddata fixtures/01_mqtt_device_families.json
python manage.py loaddata fixtures/02_mqtt_brokers.json
python manage.py loaddata fixtures/03_mqtt_topics.json
python manage.py loaddata fixtures/04_sensor_actuaciones.json
python manage.py loaddata fixtures/05_router_parameters.json

# O cargar todos a la vez (Django respetará el orden alfabético)
python manage.py loaddata fixtures/*.json
```

### En despliegue con Docker

```bash
# Cargar todos los fixtures
docker compose exec web python manage.py loaddata fixtures/01_mqtt_device_families.json
docker compose exec web python manage.py loaddata fixtures/02_mqtt_brokers.json
docker compose exec web python manage.py loaddata fixtures/03_mqtt_topics.json
docker compose exec web python manage.py loaddata fixtures/04_sensor_actuaciones.json
docker compose exec web python manage.py loaddata fixtures/05_router_parameters.json

# O cargar todos de una vez
docker compose exec web bash -c "python manage.py loaddata fixtures/*.json"
```

### Script automatizado para despliegue

Puedes crear un script que cargue todos los fixtures automáticamente:

```bash
#!/bin/bash
# load_fixtures.sh

echo "Cargando datos iniciales..."

for fixture in /app/fixtures/*.json; do
    echo "Cargando: $fixture"
    python manage.py loaddata "$fixture"
done

echo "✓ Datos iniciales cargados correctamente"
```

## Regenerar Fixtures (desde base de datos existente)

Si necesitas actualizar los fixtures desde tu base de datos actual:

### Desarrollo local
```bash
python manage.py dumpdata boreas_mediacion.MQTT_device_family --indent 2 -o fixtures/01_mqtt_device_families.json
python manage.py dumpdata boreas_mediacion.MQTT_broker --indent 2 -o fixtures/02_mqtt_brokers.json
python manage.py dumpdata boreas_mediacion.MQTT_topic --indent 2 -o fixtures/03_mqtt_topics.json
python manage.py dumpdata boreas_mediacion.sensor_actuacion --indent 2 -o fixtures/04_sensor_actuaciones.json
python manage.py dumpdata boreas_mediacion.router_parameter --indent 2 -o fixtures/05_router_parameters.json
```

### Docker (base de datos PostgreSQL)
```bash
docker compose exec web python manage.py dumpdata boreas_mediacion.MQTT_device_family --indent 2 -o /app/fixtures/01_mqtt_device_families.json
docker compose exec web python manage.py dumpdata boreas_mediacion.MQTT_broker --indent 2 -o /app/fixtures/02_mqtt_brokers.json
docker compose exec web python manage.py dumpdata boreas_mediacion.MQTT_topic --indent 2 -o /app/fixtures/03_mqtt_topics.json
docker compose exec web python manage.py dumpdata boreas_mediacion.sensor_actuacion --indent 2 -o /app/fixtures/04_sensor_actuaciones.json
docker compose exec web python manage.py dumpdata boreas_mediacion.router_parameter --indent 2 -o /app/fixtures/05_router_parameters.json

# Copiar fixtures del contenedor al host
docker compose cp web:/app/fixtures/. boreas_mediacion/fixtures/
```

## Contenido de los Fixtures

### MQTT Device Families
Familias de dispositivos IoT soportados:
- AEMET (estaciones meteorológicas)
- shellies / shellies2 (dispositivos Shelly)
- IAQ_Measures (sensores de calidad de aire)
- router (routers 4G/LTE)
- gadget (sensores Sigfox)

### MQTT Brokers
Configuración de brokers MQTT que incluye:
- Servidor y puerto
- Credenciales de acceso
- Parámetros de conexión (keepalive, etc.)

### MQTT Topics
Topics configurados para cada familia de dispositivos:
- Topics de lectura (ro - read only)
- Topics de escritura/actuación (rw - read/write)
- Configuración de QoS

### Sensor Actuaciones
Comandos disponibles para actuar sobre dispositivos:
- on/off (encendido/apagado de relés)
- Comandos específicos por tipo de sensor

### Router Parameters
Parámetros de configuración disponibles para routers:
- Estado de conexión
- Uso de datos
- Información de red

## Notas Importantes

- **Orden de carga**: Es importante respetar el orden numérico de los archivos debido a las relaciones entre modelos (Foreign Keys).
- **IDs primarios**: Los fixtures incluyen los IDs primarios (pk), por lo que se recrearán con los mismos IDs en la nueva base de datos.
- **Seguridad**: Revisa las credenciales en `02_mqtt_brokers.json` antes de cargar en producción.
- **Limpieza**: Si necesitas limpiar los datos antes de recargar, usa:
  ```bash
  python manage.py flush  # ¡CUIDADO! Borra TODA la base de datos
  ```

## Integración en el Proceso de Despliegue

Estos fixtures deben cargarse DESPUÉS de ejecutar las migraciones y ANTES de crear el superusuario:

```bash
# 1. Ejecutar migraciones
docker compose exec web python manage.py migrate

# 2. Cargar fixtures (datos básicos)
docker compose exec web bash -c "python manage.py loaddata fixtures/*.json"

# 3. Crear superusuario
docker compose exec web python manage.py createsuperuser

# 4. Collectstatic
docker compose exec web python manage.py collectstatic --noinput
```
