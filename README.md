# Boreas RGIoT - Sistema de Mediación IoT

Sistema completo de mediación y gestión de datos IoT que integra múltiples fuentes de datos (MQTT, Sigfox, DATADIS, WirelessLogic) con procesamiento automatizado mediante Apache Airflow.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Requisitos Previos](#requisitos-previos)
- [Instalación y Despliegue](#instalación-y-despliegue)
- [Configuración](#configuración)
- [Uso](#uso)
- [API](#api)
- [Mantenimiento](#mantenimiento)
- [Solución de Problemas](#solución-de-problemas)

## ✨ Características

- **Mediación MQTT**: Recepción y procesamiento de mensajes de dispositivos IoT (Shelly, sensores personalizados)
- **Integración Sigfox**: Procesamiento de datos de sensores Sigfox (CO2, temperatura, humedad)
- **DATADIS**: Consulta automática de datos de consumo eléctrico
- **WirelessLogic**: Gestión y monitoreo de SIMs M2M
- **Sistema de Alertas**: Monitoreo automático y notificaciones por email/MQTT
- **Apache Airflow**: Automatización de tareas de recolección y procesamiento de datos
- **API REST**: Interfaz completa para acceso a datos y actuaciones
- **Panel de Administración**: Django Admin personalizado para gestión

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (Puerto 80)                    │
│                    Reverse Proxy / Static Files              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Django App (Puerto 8000)                       │
│  - API REST (Django REST Framework)                         │
│  - Panel de Administración                                  │
│  - Sistema de Alertas                                       │
│  - Servicios de Integración (DATADIS, WirelessLogic, etc)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           PostgreSQL (Puerto 5432)                          │
│  - Base de datos compartida Django/Airflow                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         Apache Airflow (Puerto 8080)                        │
│  - Scheduler: Ejecución automática de DAGs                 │
│  - Webserver: Interfaz de monitoreo                        │
│  - DAGs: aemet_monitor, boreas_alerts                      │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

- **Django Web App**: Aplicación principal con API REST y panel de administración
- **PostgreSQL**: Base de datos relacional compartida
- **Nginx**: Servidor web para servir archivos estáticos y proxy reverso
- **Apache Airflow**: Orquestador de tareas programadas
- **MQTT**: Protocolo de comunicación para dispositivos IoT

## 📦 Requisitos Previos

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Puertos disponibles: 80, 5432, 8000, 8080

## 🚀 Instalación y Despliegue

### 1. Clonar el Repositorio

```bash
git clone https://github.com/alonsoggpablo/boreas_rgiot.git
cd boreas_rgiot
```

### 2. Configurar Variables de Entorno

Crear archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
# Django
DEBUG=False
SECRET_KEY=tu-clave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com

# Base de datos
DATABASE_URL=postgresql://boreas_user:boreas_password@db:5432/boreas_db
POSTGRES_DB=boreas_db
POSTGRES_USER=boreas_user
POSTGRES_PASSWORD=tu-password-seguro

# MQTT
MQTT_BROKER=mqtt.tu-broker.com
MQTT_PORT=8883
MQTT_USERNAME=tu-usuario
MQTT_PASSWORD=tu-password

# Email
EMAIL_HOST=smtp.tu-servidor.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@dominio.com
EMAIL_HOST_PASSWORD=tu-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=tu-email@dominio.com
```

### 3. Desplegar con Docker Compose

**Opción A: Solo Django + PostgreSQL + Nginx**

```bash
docker-compose up -d
```

**Opción B: Stack completo con Airflow**

```bash
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml up -d --build
```

### 4. Ejecutar Migraciones

```bash
docker-compose exec web python manage.py migrate
```

### 5. Crear Superusuario

```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Cargar Datos Iniciales (Opcional)

```bash
docker-compose exec web python manage.py loaddata fixtures/01_mqtt_device_families.json
docker-compose exec web python manage.py loaddata fixtures/02_mqtt_brokers.json
docker-compose exec web python manage.py loaddata fixtures/03_mqtt_topics.json
docker-compose exec web python manage.py loaddata fixtures/04_sensor_actuaciones.json
docker-compose exec web python manage.py loaddata fixtures/05_router_parameters.json
```

## ⚙️ Configuración

### Acceso a Servicios

- **Django Admin**: http://localhost/admin
- **API REST**: http://localhost/api/
- **Airflow Web UI**: http://localhost:8080 (usuario: `airflow`, contraseña: `airflow`)
- **Django App**: http://localhost:8000 (directo, sin nginx)

### Configurar MQTT Topics

1. Acceder al panel de administración
2. Ir a "MQTT brokers" y crear/configurar brokers
3. Ir a "MQTT topics" y configurar los topics a suscribir
4. Activar los topics necesarios

### Configurar Alertas

1. Ir a "Alert Rules" en el admin
2. Crear reglas de alerta:
   - Disk Space: Alerta cuando el disco supera un umbral
   - Device Connection: Alerta cuando un dispositivo no reporta
   - AEMET Data: Alerta para datos meteorológicos
3. Configurar destinatarios de email

## � Sistema de Alertas

El sistema de alertas permite monitorear automáticamente diferentes aspectos del sistema y enviar notificaciones cuando se detectan condiciones anormales.

### Tipos de Alertas

#### 1. Disk Space (Espacio en Disco)

Monitorea el uso del disco y genera alertas cuando supera un umbral.

**Configuración:**
```python
Tipo: disk_space
Umbral: 89 (%)
Intervalo de verificación: 60 minutos
Destinatarios: admin@dominio.com, ops@dominio.com
```

**Ejemplo de uso:**
1. Acceder a Django Admin → Alert Rules
2. Crear nueva regla:
   - Nombre: "Alerta Disco Lleno"
   - Tipo: Disk Space
   - Umbral: 85
   - Intervalo: 30 minutos
   - Notificación: email
   - Destinatarios: admin@ejemplo.com

#### 2. Device Connection (Conexión de Dispositivos)

Detecta cuando dispositivos IoT dejan de reportar datos.

**Configuración:**
```python
Tipo: device_connection
Configuración JSON: {
  "device_id": "shellyem3-BCFF4DFD1732",
  "max_silence_minutes": 60
}
Destinatarios: iot@dominio.com
```

#### 3. AEMET Data (Datos Meteorológicos)

Verifica que los datos de AEMET se reciben correctamente.

**Configuración:**
```python
Tipo: aemet_data
Configuración JSON: {
  "station_id": "5514X",
  "max_age_hours": 3
}
```

### Estados de Alertas

- **active**: Alerta activa que requiere atención
- **acknowledged**: Alerta reconocida por un operador
- **resolved**: Problema resuelto, alerta cerrada

### Niveles de Severidad

- **info**: Información general
- **warning**: Advertencia, requiere revisión
- **error**: Error que afecta funcionalidad
- **critical**: Crítico, requiere atención inmediata

### Gestión de Alertas vía API

```bash
# Listar alertas activas
curl http://localhost/api/alerts/?status=active

# Reconocer una alerta
curl -X PATCH http://localhost/api/alerts/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "acknowledged"}'

# Resolver una alerta
curl -X PATCH http://localhost/api/alerts/1/ \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved"}'

# Crear alerta personalizada
curl -X POST http://localhost/api/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "custom",
    "severity": "warning",
    "message": "Temperatura alta en sala de servidores",
    "details": {
      "temperature": 35,
      "location": "Server Room A",
      "sensor_id": "temp-001"
    }
  }'
```

### Notificaciones

El sistema soporta dos tipos de notificaciones:

1. **Email**: Envío de correos mediante SMTP
2. **MQTT**: Publicación de mensajes en topics MQTT

**Configuración de notificaciones por email:**
- Configurar variables de entorno: `EMAIL_HOST`, `EMAIL_PORT`, etc.
- Especificar destinatarios en la regla de alerta (separados por comas)

**Configuración de notificaciones por MQTT:**
```python
Tipo de notificación: mqtt
Configuración JSON: {
  "topic": "alerts/critical",
  "qos": 1
}
```

## ⏰ Apache Airflow - DAGs

Apache Airflow gestiona la ejecución programada de tareas de recolección y procesamiento de datos.

### DAGs Disponibles

#### 1. aemet_data_monitor

Monitorea y recopila datos meteorológicos de AEMET.

**Descripción:**
- **Frecuencia**: Cada 3 horas
- **Función**: Consulta API de AEMET y almacena datos meteorológicos
- **Estaciones monitoreadas**: Configurables en el código

**Tareas del DAG:**
1. `check_api_status`: Verifica disponibilidad de API AEMET
2. `fetch_weather_data`: Descarga datos meteorológicos
3. `store_data`: Almacena en base de datos
4. `check_alerts`: Verifica condiciones de alerta

**Configuración:**
```python
# Ubicación: airflow/dags/aemet_monitor.py
default_args = {
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

schedule_interval = '0 */3 * * *'  # Cada 3 horas
```

**Activar DAG:**
1. Acceder a Airflow UI: http://localhost:8080
2. Buscar "aemet_data_monitor"
3. Activar el toggle
4. Opcional: ejecutar manualmente con "Trigger DAG"

#### 2. boreas_alerts

Ejecuta verificaciones periódicas de reglas de alerta.

**Descripción:**
- **Frecuencia**: Cada 15 minutos
- **Función**: Evalúa todas las reglas de alerta activas y genera notificaciones

**Tareas del DAG:**
1. `load_alert_rules`: Carga reglas activas de la base de datos
2. `check_disk_space`: Verifica espacio en disco
3. `check_device_connections`: Verifica conectividad de dispositivos
4. `check_aemet_data`: Verifica frescura de datos AEMET
5. `send_notifications`: Envía notificaciones para alertas nuevas

**Configuración:**
```python
# Ubicación: airflow/dags/boreas_alerts.py
schedule_interval = '*/15 * * * *'  # Cada 15 minutos
```

**Monitoreo:**
- Ver ejecuciones en Airflow UI → DAG Runs
- Logs detallados en cada tarea
- Métricas de éxito/fallo

### Gestión de DAGs

#### Ver logs de ejecución

```bash
# Logs del scheduler
docker-compose logs -f airflow-scheduler

# Logs de una ejecución específica (desde Airflow UI)
# DAG → DAG Runs → Click en fecha → View Log
```

#### Ejecutar DAG manualmente

```bash
# Opción 1: Desde Airflow UI
# Click en DAG → Trigger DAG → Confirm

# Opción 2: Desde línea de comandos
docker-compose exec airflow-scheduler airflow dags trigger aemet_data_monitor
docker-compose exec airflow-scheduler airflow dags trigger boreas_alerts
```

#### Pausar/Reanudar DAG

```bash
# Pausar
docker-compose exec airflow-scheduler airflow dags pause aemet_data_monitor

# Reanudar
docker-compose exec airflow-scheduler airflow dags unpause aemet_data_monitor
```

#### Configurar alertas de Airflow

En `airflow/dags/aemet_monitor.py`:

```python
default_args = {
    'email': ['admin@ejemplo.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}
```

### Crear un DAG Personalizado

1. Crear archivo en `airflow/dags/mi_dag_personalizado.py`:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def mi_tarea():
    print("Ejecutando mi tarea personalizada")
    # Tu lógica aquí

default_args = {
    'owner': 'boreas',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'mi_dag_personalizado',
    default_args=default_args,
    description='Mi DAG personalizado',
    schedule_interval='@daily',  # Diario
    catchup=False,
)

tarea = PythonOperator(
    task_id='ejecutar_tarea',
    python_callable=mi_tarea,
    dag=dag,
)
```

2. Reiniciar scheduler para detectar nuevo DAG:

```bash
docker-compose restart airflow-scheduler
```

3. Verificar en Airflow UI que el DAG aparece

### Mejores Prácticas para DAGs

- **Idempotencia**: Las tareas deben poder ejecutarse múltiples veces sin efectos secundarios
- **Atomicidad**: Cada tarea debe ser una unidad atómica de trabajo
- **Logging**: Usar logging adecuado para depuración
- **Manejo de errores**: Implementar reintentos y manejo de excepciones
- **Testing**: Probar DAGs antes de desplegar en producción

## �📚 Uso

### API REST - Endpoints Principales

```bash
# Listar mensajes MQTT
GET /api/mqtt-messages/

# Obtener medidas reportadas
GET /api/reported-measures/

# Listar dispositivos Sigfox
GET /api/sigfox-devices/

# Obtener lecturas Sigfox
GET /api/sigfox-readings/

# Listar SIMs WirelessLogic
GET /api/wirelesslogic-sims/

# Obtener consumos DATADIS
GET /api/datadis-consumptions/

# Listar alertas activas
GET /api/alerts/?status=active

# Ejecutar comando en dispositivo
POST /api/sensor-commands/
{
  "actuacion": 1,
  "device_id": "shellyem3-BCFF4DFD1732",
  "circuit": 0
}
```

### Ejemplos con curl

```bash
# Obtener todos los mensajes MQTT (requiere autenticación)
curl -u usuario:password http://localhost/api/mqtt-messages/

# Crear alerta manual
curl -X POST http://localhost/api/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "custom",
    "severity": "warning",
    "message": "Alerta de prueba",
    "details": {"source": "manual"}
  }'
```

## 🔧 Mantenimiento

### Ver Logs

```bash
# Logs de todos los servicios
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml logs -f

# Logs de un servicio específico
docker-compose logs -f web
docker-compose logs -f airflow-scheduler
```

### Backup de Base de Datos

```bash
# Crear backup
docker-compose exec -T db pg_dump -U boreas_user boreas_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker-compose exec -T db psql -U boreas_user -d boreas_db < backup_20260113_120000.sql
```

### Actualizar el Sistema

```bash
# Detener servicios
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml down

# Obtener últimos cambios
git pull

# Reconstruir y reiniciar
docker-compose -f docker-compose.yml -f docker-compose.airflow.yml up -d --build

# Ejecutar migraciones
docker-compose exec web python manage.py migrate
```

### Acceso a la Base de Datos

```bash
# Conectar a PostgreSQL
docker-compose exec db psql -U boreas_user -d boreas_db
```

### Recolectar Archivos Estáticos

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

## 🐛 Solución de Problemas

### Los contenedores no inician

```bash
# Verificar estado
docker-compose ps

# Ver logs de error
docker-compose logs web

# Reconstruir desde cero
docker-compose down -v
docker-compose up -d --build
```

### Error de migración de base de datos

```bash
# Eliminar migraciones conflictivas (¡CUIDADO!)
docker-compose exec web python manage.py migrate --fake boreas_mediacion zero
docker-compose exec web python manage.py migrate
```

### Problemas de conexión MQTT

1. Verificar configuración en `.env`
2. Comprobar que el broker MQTT es accesible
3. Revisar logs: `docker-compose logs web | grep mqtt`

### Airflow no ejecuta DAGs

1. Verificar que el scheduler está corriendo: `docker-compose ps airflow-scheduler`
2. Activar DAGs en la UI de Airflow
3. Revisar logs: `docker-compose logs airflow-scheduler`

### Error "IndentationError" en models.py

Este error ya fue corregido. Si persiste:
- Verificar que los campos en models.py tienen indentación correcta (4 espacios)
- Reconstruir contenedores: `docker-compose up -d --build`

## 📄 Licencia

Este proyecto es privado y propiedad de RG Gestión y Energía.

## 👥 Contacto

- Email: alonsogpablo@rggestionyenergia.com
- Repositorio: https://github.com/alonsoggpablo/boreas_rgiot

## 🔄 Changelog

### v1.0.0 (2026-01-13)
- ✅ Configuración de docker-compose para base de datos compartida
- ✅ Corrección de defaults en todos los modelos
- ✅ Eliminación de servicios duplicados en docker-compose.airflow.yml
- ✅ Corrección de errores de indentación en models.py
- ✅ Sistema de alertas funcional
- ✅ Integración completa con Airflow
