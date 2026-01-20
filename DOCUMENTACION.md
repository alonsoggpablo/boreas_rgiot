# 🚀 Despliegue y Operaciones

### Despliegue Completo (`full_deploy.sh`)

El script `full_deploy.sh` realiza un despliegue limpio y completo del sistema:

1. Descarga la última versión del código (`git pull`).
2. Detiene y elimina todos los contenedores y volúmenes de datos.
3. Elimina migraciones antiguas para un historial limpio.
4. Reconstruye todos los contenedores (web, Airflow, base de datos, nginx).
5. Inicia primero la base de datos, luego los servicios web y Airflow.
6. Inicia el proxy nginx.

**Uso:**
```bash
./full_deploy.sh
```
> ⚠️ Este script borra la base de datos y migraciones. Úsalo solo para despliegues limpios o entornos de desarrollo.

---

### Recargar Airflow (`reload_airflow.sh`)

El script `reload_airflow.sh` reinicia los servicios de Airflow (webserver y scheduler) para aplicar cambios en los DAGs o configuración.

**Uso:**
```bash
./reload_airflow.sh
```
- Reinicia los contenedores `airflow-webserver` y `airflow-scheduler`.
- Útil tras modificar DAGs o variables de entorno relacionadas con Airflow.

---

### Actualización de la Aplicación (`update_deployment.sh`)

El script `update_deployment.sh` actualiza el sistema sin borrar la base de datos:

1. Descarga los últimos cambios (`git pull`).
2. Detiene los contenedores.
3. Reconstruye el contenedor web.
4. Inicia la base de datos y espera a que esté lista.
5. Recoge archivos estáticos (`collectstatic`).
6. Inicia los servicios web y nginx.

**Uso:**
```bash
./update_deployment.sh
```
- No borra datos ni migraciones.
- Ideal para actualizaciones en producción.

---

## 🗂️ Estructura de la Aplicación

```
boreas_rgiot/
├── boreas_mediacion/           # App Django principal (modelos, vistas, admin, lógica de negocio)
│   ├── boreas_mediacion/       # Código fuente Django (models, admin, services)
│   ├── management/             # Comandos personalizados Django
│   ├── fixtures/               # Datos iniciales (JSON)
│   ├── static/                 # Archivos estáticos (CSS, JS)
│   ├── templates/              # Plantillas HTML
│   └── ...
├── airflow/                    # Orquestación de tareas (Apache Airflow)
│   ├── dags/                   # DAGs de Airflow (automatización)
│   ├── logs/                   # Logs de ejecución de DAGs
│   └── plugins/                # Plugins personalizados
├── scripts/                    # Scripts de despliegue y utilidades
├── requirements.txt            # Dependencias Python
├── docker-compose.yml          # Servicios principales (web, db, nginx)
├── docker-compose.airflow.yml  # Servicios Airflow
├── full_deploy.sh              # Despliegue completo
├── update_deployment.sh        # Actualización
├── reload_airflow.sh           # Recarga Airflow
└── ...
```

---

## ⚙️ Lógica de la Aplicación

- **MQTT:** Recepción y almacenamiento de mensajes de dispositivos IoT.
- **API REST:** Consulta y gestión de datos históricos, configuración y comandos.
- **Alertas:** Reglas configurables para notificaciones automáticas.
- **Integraciones:** WirelessLogic (SIMs), DATADIS (consumo eléctrico), Sigfox (sensores).
- **Panel Admin:** Gestión avanzada de modelos y acciones personalizadas.

---

## ⏰ Automatización con Airflow (DAGs)

Los DAGs de Airflow automatizan tareas clave:

- `aemet_monitor.py`: Monitorea datos meteorológicos AEMET, envía alertas si faltan datos.
- `boreas_alerts.py`: Ejecuta reglas de alertas (conexión, espacio en disco, etc.).
- `datadis_api_read.py`: Sincroniza puntos de suministro desde la API DATADIS a la base de datos.
- Otros DAGs pueden incluir integración con Sigfox, WirelessLogic, etc.

**Ubicación:**  
`airflow/dags/`

**Recarga de DAGs:**  
Tras modificar un DAG, ejecutar:
```bash
./reload_airflow.sh
```
y verificar en la UI de Airflow (http://localhost:8080).
# BOREAS RGIOT - Documentación del Proyecto

## 📋 Descripción General

**BOREAS RGIOT** es una plataforma Django para **recolección, procesamiento y visualización de datos de sensores IoT** a través del protocolo **MQTT**. El proyecto integra dispositivos inteligentes Shelly (relés, medidores de energía) con una API REST para monitoreo y control remoto.

**Stack Tecnológico:**
- Django 4.2 + Django REST Framework
- PostgreSQL 15 (base de datos)
- MQTT (protocolo de comunicación IoT)
- Node-Red (orquestación de flujos)
- Docker + Nginx (despliegue)

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│         DISPOSITIVOS INTELIGENTES SHELLY             │
│  (ShellyEM3, Shelly1PM, ShellyEM - sensores/relés)  │
└────────────────┬────────────────────────────────────┘
                 │ MQTT
                 ↓
┌─────────────────────────────────────────────────────┐
│           BROKER MQTT (RGIOT)                        │
│  Recibe datos de sensores en topics estructurados   │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
  ┌──────────────┐  ┌──────────────┐
  │  Django App  │  │  Node-Red    │
  │  + Postgres  │  │  (flujos)    │
  └──────┬───────┘  └──────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────┐
│        API REST (DRF)                                │
│  - Consultar datos históricos                       │
│  - Publicar comandos a dispositivos                 │
│  - Gestionar configuración de brokers/topics        │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Modelos de Datos

### 1. **mqtt_msg** - Mensajes MQTT Recibidos
Almacena todos los mensajes MQTT capturados del broker.

```
- report_time: Timestamp automático de recepción
- device: JSON con información del dispositivo
- device_id: ID único del dispositivo (ej: "shelly1pm-E8DB84D79ABD")
- measures: JSON con datos de medición (temperatura, energía, etc.)
- feed: Tipo de feed (ej: "shellies", "router")
```

### 2. **reported_measure** - Medidas Reportadas
Almacena medidas específicas reportadas por dispositivos.

```
- report_time: Timestamp automático
- device: JSON con info del dispositivo
- device_id: ID del dispositivo
- measures: Datos de medición procesados
- feed: Tipo de feed
```

### 3. **MQTT_broker** - Configuración de Brokers
Define los servidores MQTT a los que conectarse.

```
- name: Nombre del broker (ej: "rgiot")
- server: Dirección IP/dominio del broker
- port: Puerto MQTT (default: 1883)
- keepalive: Tiempo de keep-alive en segundos
- description: Descripción del broker
- active: Boolean para activar/desactivar
- user: Usuario de autenticación MQTT
- password: Contraseña de autenticación MQTT
```

### 4. **MQTT_device_family** - Familias de Dispositivos
Categorías de dispositivos (ej: Shelly, Router, etc.)

```
- name: Nombre de la familia
```

### 5. **MQTT_topic** - Topics MQTT a Suscribirse
Define qué topics MQTT escuchar y cómo procesarlos.

```
- broker: Referencia al broker MQTT
- family: Familia de dispositivos
- topic: Path del topic (ej: "shellies/shelly1pm-+/relay/0")
- qos: Quality of Service (0, 1, o 2)
- description: Descripción del topic
- active: Boolean para activar/desactivar
- ro_rw: Read-Only (ro) o Read-Write (rw)
```

### 6. **MQTT_feed** - Feeds de Datos
Define campos específicos de datos dentro de topics.

```
- name: Nombre del feed (ej: "power", "temperature")
- description: Descripción
- topic: Referencia al MQTT_topic
```

### 7. **MQTT_tx** - Mensajes a Transmitir
Cola de mensajes para enviar a dispositivos.

```
- topic: Topic destino
- payload: Carga útil del mensaje
```

### 8. **sensor_actuacion** - Tipos de Actuaciones
Define acciones disponibles sobre sensores/actuadores.

```
- tipo: Tipo de actuación (ej: "relay", "led")
- command: Comando a enviar (ej: "on", "off")
- parameter: Parámetro del comando
- description: Descripción
```

### 9. **sensor_command** - Comandos de Sensores
Ordena ejecutar una actuación en un dispositivo específico.

```
- actuacion: Referencia a sensor_actuacion
- device_id: Dispositivo destino
- circuit: Número de circuito (para relés múltiples)
```

### 10. **router_parameter** - Parámetros de Router
Define parámetros configurables de routers.

```
- parameter: Nombre del parámetro
- description: Descripción
```

### 11. **router_get** - Consultas de Router
Solicitudes de parámetros específicos de routers.

```
- parameter: Referencia a router_parameter
- device_id: Router específico
```

---

## 🔌 Flujo de Datos MQTT

### Recepción de Datos (Suscripción)

1. **Cliente MQTT se conecta** al broker definido en `MQTT_broker`
2. **Se suscribe** a todos los topics en `MQTT_topic` que estén activos
3. **Al recibir mensaje**:
   - Se parsea el topic (ej: `shellies/shelly1pm-E8DB84D79ABD/relay/0`)
   - Se parsea el payload JSON
   - Se crea/actualiza un registro en `mqtt_msg`
   - Se procesa la información según `MQTT_feed`
   - Se pueden disparar `sensor_command` automáticos

### Transmisión de Datos (Publicación)

1. **Usuario solicita acción** (vía API REST)
2. **Se crea** un registro en `sensor_command`
3. **Función signal post_save** detecta el nuevo comando
4. **Se publica** a través del cliente MQTT al topic correspondiente
5. **Dispositivo** recibe y ejecuta la acción

---

## 🌐 API REST Endpoints

### Listar Mensajes MQTT
```
GET /api/mqtt_msg/
GET /api/mqtt_msg/?device_id=shelly1pm-E8DB84D79ABD
```
Filtrable por device_id. Requiere autenticación.

### Listar Medidas Reportadas
```
GET /api/reported_measure/
GET /api/reported_measure/?device_id=shelly1pm-E8DB84D79ABD
```

### Publicar Comando a Dispositivo
```
POST /api/publish/
Content-Type: application/json

{
  "topic": "shellies/shelly1pm-E8DB84D79ABD/command",
  "payload": "{\"relay\": {\"0\": {\"on\": true}}}"
}
```

### Gestionar MQTT Brokers
```
GET /api/mqtt_broker/
POST /api/mqtt_broker/
PUT /api/mqtt_broker/{id}/
DELETE /api/mqtt_broker/{id}/
```

---

## 📁 Estructura de Carpetas

```
boreas_rgiot/
├── README.md                          # Descripción breve
├── requirements.txt                   # Dependencias Python
├── DOCUMENTACION.md                   # Este archivo
├── Dockerfile                         # Para deployment con Docker
├── docker-compose.yml                 # Orquestación de servicios
├── .env.example                       # Variables de entorno
│
└── boreas_mediacion/
    ├── manage.py                      # Script de gestión Django
    ├── db.sqlite3                     # DB local (para desarrollo)
    ├── run_manage.bat                 # Script para Windows
    ├── web.config                     # Configuración IIS
    │
    ├── boreas_mediacion/              # Aplicación principal
    │   ├── __init__.py                # Inicializa cliente MQTT
    │   ├── settings.py                # Configuración Django
    │   ├── urls.py                    # Rutas de URLs
    │   ├── wsgi.py                    # Interfaz WSGI
    │   ├── asgi.py                    # Interfaz ASGI
    │   ├── models.py                  # Definición de modelos
    │   ├── views.py                   # Vistas REST API
    │   ├── serializers.py             # Serializadores DRF
    │   ├── mqtt.py                    # Lógica MQTT (cliente)
    │   ├── admin.py                   # Interfaz Django Admin
    │   ├── migrations/                # Migraciones de base de datos
    │   └── __pycache__/
    │
    ├── node_red_files/
    │   ├── function.js                # Funciones Node-Red
    │   └── mqtt_output_tt.json        # Flujo de salida MQTT
    │
    ├── sample_json_files/             # Datos de ejemplo
    │   ├── shelly1pm-*.json           # Mensajes de ejemplo Shelly1PM
    │   ├── shellyem3-*.json           # Mensajes de ejemplo ShellyEM3
    │   └── ...
    │
    └── static/                        # Archivos estáticos (CSS, JS)
```

---

## 🚀 Funcionalidades Principales

### 1. **Monitoreo de Sensores en Tiempo Real**
- Recibe datos continuamente de dispositivos Shelly
- Almacena histórico completo en PostgreSQL
- Filtra por dispositivo vía API

### 2. **Control Remoto de Dispositivos**
- Enciende/apaga relés remotamente
- Configura parámetros de dispositivos
- Historial de comandos ejecutados

### 3. **Gestión Multi-Broker**
- Soporte para múltiples brokers MQTT
- Activar/desactivar brokers sin reiniciar
- Autenticación por usuario/contraseña

### 4. **Configuración Flexible de Topics**
- Suscribirse a topics personalizados
- Mapeo de topics a modelos de datos
- QoS configurable por topic

### 5. **Automatización con Node-Red**
- Flujos de procesamiento de datos
- Disparadores de acciones basadas en condiciones
- Integración con servicios externos

### 6. **Interfaz de Administración**
- Panel Django Admin para gestionar configuración
- Usuario/contraseña para API REST
- Auditoría de acciones

---

## 🔧 Instalación y Despliegue

### Opción 1: Docker (Recomendado)

```bash
# Construir y levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser
```

### Opción 2: Local (Desarrollo)

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

---

## 📝 Configuración Requerida

### Variables de Entorno (`.env`)

```env
# Django
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/boreas_rgiot

# MQTT
MQTT_BROKER=broker.example.com
MQTT_PORT=1883
MQTT_USER=mqtt_user
MQTT_PASSWORD=mqtt_password
```

### Configurar en Django Admin

1. **Crear MQTT Broker**
   - Ir a `/admin/boreas_mediacion/mqtt_broker/`
   - Crear nuevo broker con datos del servidor MQTT

2. **Crear Device Families**
   - Ir a `/admin/boreas_mediacion/mqtt_device_family/`
   - Crear: "Shelly", "Router", etc.

3. **Crear MQTT Topics**
   - Ir a `/admin/boreas_mediacion/mqtt_topic/`
   - Ejemplo: `shellies/shelly1pm-+/relay/0`

---

## 📊 Ejemplos de Datos Shelly

### ShellyEM3 (Medidor de Energía Trifásico)
```json
{
  "device_id": "shellyem3-BCFF4DFD1732",
  "measure": {
    "power": 2500,           // Potencia en watts
    "energy": 1234567,       // Energía en Wh
    "voltage": 230,          // Voltaje en V
    "current": 10.8,         // Corriente en A
    "pf": 0.95               // Factor de potencia
  }
}
```

### Shelly1PM (Relé con Medición)
```json
{
  "device_id": "shelly1pm-E8DB84D79ABD",
  "measure": {
    "relay_0": true,         // Estado del relé
    "power": 500,            // Potencia consumida
    "temperature": 45,       // Temperatura interna
    "ext_temperature": 22    // Temperatura exterior
  }
}
```

---

## 🔐 Seguridad

- **Autenticación**: Basada en usuario/contraseña Django
- **MQTT**: Soporta autenticación usuario/contraseña y TLS
- **API**: Token de autenticación para aplicaciones externas
- **Base de datos**: Contraseña fuerte y conexión cifrada en producción

---

## 📞 Soporte

Para más información sobre:
- **Dispositivos Shelly**: https://shelly.cloud/
- **MQTT**: https://mqtt.org/
- **Django**: https://www.djangoproject.com/
- **Node-Red**: https://nodered.org/

---

**Última actualización**: Enero 2026
**Versión**: 1.0
