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

## 📚 Uso

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
