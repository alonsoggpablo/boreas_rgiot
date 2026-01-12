# Apache Airflow - Orquestación de Tareas Boreas RGIOT

Este directorio contiene la configuración de Apache Airflow para automatizar tareas programadas del sistema Boreas RGIOT.

## ¿Qué es Apache Airflow?

Apache Airflow es una plataforma de orquestación de flujos de trabajo que permite programar, monitorear y gestionar tareas complejas de forma automática.

## DAGs Implementados

### 1. `aemet_monitor.py` - Monitor de Datos AEMET
**Propósito:** Monitorear la recepción de datos meteorológicos de AEMET

**Programación:** Cada 5 minutos

**Tareas:**
- Verifica si se han recibido nuevos datos de estaciones AEMET
- Envía notificaciones por email cuando se detectan nuevos datos
- Ejecuta el comando Django: `check_aemet_data`

**Configuración necesaria:**
- Recipient email configurado en el código o variable de Airflow

### 2. `boreas_alerts.py` - Sistema de Alertas Automáticas
**Propósito:** Ejecutar verificaciones automáticas y enviar alertas

**Programación:** Diariamente a las 02:00, 09:00 y 10:00

**Tareas:**
- **02:00** - Limpieza de alertas antiguas
- **09:00** - Verificación de conexión de dispositivos
- **10:00** - Verificación de espacio en disco

**Configuración necesaria:**
- Reglas de alerta configuradas en Django Admin
- Emails de notificación configurados

## Estructura de Archivos

```
airflow/
├── dags/                  # DAGs (Directed Acyclic Graphs)
│   ├── aemet_monitor.py   # Monitoreo AEMET
│   ├── boreas_alerts.py   # Sistema de alertas
│   └── __pycache__/       # Cache de Python (automático)
├── logs/                  # Logs de ejecución (generados automáticamente)
│   ├── dag_id=aemet_data_monitor/
│   ├── dag_id=boreas_alerts/
│   ├── dag_processor_manager/
│   └── scheduler/
├── plugins/               # Plugins personalizados de Airflow
└── config.py             # Configuración personalizada (si existe)
```

## Despliegue con Docker

### Iniciar Airflow

```bash
# Desde el directorio raíz del proyecto
docker compose -f docker-compose.airflow.yml up -d
```

### Verificar Estado

```bash
# Ver contenedores
docker compose -f docker-compose.airflow.yml ps

# Ver logs
docker compose -f docker-compose.airflow.yml logs -f
```

### Acceder a la Interfaz Web

- **URL:** http://localhost:8080 (o http://tu-servidor:8080)
- **Usuario:** airflow
- **Contraseña:** airflow

## Carga Automática de DAGs

Los DAGs se cargan **automáticamente** desde el directorio `./airflow/dags/`:

1. Los archivos están montados como volumen en Docker
2. Airflow escanea el directorio cada 30-60 segundos
3. NO es necesario copiar archivos manualmente al contenedor
4. Los cambios en archivos se detectan automáticamente

### Proceso de Carga

```
./airflow/dags/*.py  →  montado como volumen  →  /opt/airflow/dags/  →  Airflow los carga
```

## Modificar o Agregar DAGs

### Editar DAG Existente

```bash
# 1. Editar archivo localmente
nano airflow/dags/aemet_monitor.py

# 2. Guardar cambios

# 3. Airflow detectará cambios automáticamente en 30-60 segundos
# O forzar recarga:
docker compose -f docker-compose.airflow.yml restart airflow-scheduler
```

### Crear Nuevo DAG

```bash
# 1. Crear archivo en airflow/dags/
nano airflow/dags/mi_nuevo_dag.py

# 2. Definir el DAG siguiendo la estructura de ejemplos existentes

# 3. Verificar sintaxis
python -m py_compile airflow/dags/mi_nuevo_dag.py

# 4. Airflow lo cargará automáticamente
```

### Ejemplo de DAG Básico

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'boreas',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'mi_dag',
    default_args=default_args,
    description='Descripción de mi DAG',
    schedule_interval='0 12 * * *',  # Diariamente a las 12:00
    catchup=False,
)

tarea1 = BashOperator(
    task_id='mi_tarea',
    bash_command='echo "Hola desde Airflow"',
    dag=dag,
)
```

## Comandos Útiles

### Gestión de DAGs

```bash
# Listar todos los DAGs
docker compose -f docker-compose.airflow.yml exec airflow-webserver airflow dags list

# Detalles de un DAG
docker compose -f docker-compose.airflow.yml exec airflow-webserver airflow dags show aemet_data_monitor

# Listar tareas de un DAG
docker compose -f docker-compose.airflow.yml exec airflow-webserver airflow tasks list aemet_data_monitor

# Ejecutar DAG manualmente
docker compose -f docker-compose.airflow.yml exec airflow-webserver airflow dags trigger aemet_data_monitor

# Pausar/Despausar DAG
docker compose -f docker-compose.airflow.yml exec airflow-webserver airflow dags pause aemet_data_monitor
docker compose -f docker-compose.airflow.yml exec airflow-webserver airflow dags unpause aemet_data_monitor
```

### Gestión de Usuarios

```bash
# Crear nuevo usuario
docker compose -f docker-compose.airflow.yml exec airflow-webserver \
  airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin123

# Listar usuarios
docker compose -f docker-compose.airflow.yml exec airflow-webserver airflow users list

# Cambiar contraseña
docker compose -f docker-compose.airflow.yml exec airflow-webserver \
  airflow users reset-password --username airflow
```

### Logs y Debug

```bash
# Ver logs del scheduler
docker compose -f docker-compose.airflow.yml logs -f airflow-scheduler

# Ver logs del webserver
docker compose -f docker-compose.airflow.yml logs -f airflow-webserver

# Ver logs de un DAG específico (desde la interfaz web es más fácil)
# O desde terminal:
docker compose -f docker-compose.airflow.yml exec airflow-webserver \
  airflow tasks test aemet_data_monitor check_aemet_task 2026-01-12
```

## Variables y Configuración

### Variables en Airflow

Se pueden configurar variables globales para los DAGs:

**Desde la Interfaz Web:**
1. Admin → Variables
2. Click en "+" para agregar
3. Definir key y value

**Desde CLI:**
```bash
docker compose -f docker-compose.airflow.yml exec airflow-webserver \
  airflow variables set aemet_recipient_email admin@example.com
```

**Usar en DAG:**
```python
from airflow.models import Variable

email = Variable.get("aemet_recipient_email")
```

### Connections (Conexiones)

Para conectar con servicios externos:

**Desde Interfaz Web:**
Admin → Connections → "+"

**Desde CLI:**
```bash
docker compose -f docker-compose.airflow.yml exec airflow-webserver \
  airflow connections add my_db \
  --conn-type postgres \
  --conn-host db \
  --conn-login user \
  --conn-password pass \
  --conn-port 5432
```

## Integración con Django

Los DAGs de Boreas están integrados con Django para:
- Acceder a modelos de la base de datos
- Ejecutar comandos de gestión Django
- Reutilizar servicios y lógica de negocio

### Configuración de Django en DAGs

```python
import os
import sys
import django

# Agregar ruta de Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

# Ahora puedes importar modelos
from boreas_mediacion.models import mqtt_msg, Alert
```

## Programación de Tareas (Cron)

Las tareas se programan usando expresiones cron:

```python
# Ejemplos de schedule_interval:

'@hourly'           # Cada hora
'@daily'            # Diariamente a medianoche
'@weekly'           # Semanalmente
'0 */2 * * *'       # Cada 2 horas
'*/5 * * * *'       # Cada 5 minutos
'0 8 * * 1-5'       # Lunes a viernes a las 8 AM
'0 2,9,10 * * *'    # Diariamente a las 2 AM, 9 AM y 10 AM
```

## Troubleshooting

### DAG no aparece en la interfaz

1. Verificar sintaxis Python: `python -m py_compile airflow/dags/mi_dag.py`
2. Ver logs del scheduler: `docker compose -f docker-compose.airflow.yml logs airflow-scheduler`
3. Verificar que el archivo está en `./airflow/dags/`
4. Reiniciar scheduler: `docker compose -f docker-compose.airflow.yml restart airflow-scheduler`

### DAG con errores

1. Revisar logs en la interfaz web (Graph view → Task → Log)
2. Verificar imports y dependencias
3. Comprobar que Django está configurado correctamente
4. Verificar permisos de archivos

### Tareas fallan

1. Ver logs específicos de la tarea en la interfaz web
2. Verificar conectividad con servicios externos
3. Comprobar que el contenedor 'db' está corriendo
4. Verificar variables de entorno y .env

## Backup y Restauración

### Backup de Metadata de Airflow

```bash
# Backup de base de datos de Airflow
docker compose -f docker-compose.airflow.yml exec airflow-db \
  pg_dump -U airflow airflow > airflow_backup_$(date +%Y%m%d).sql

# Restaurar
docker compose -f docker-compose.airflow.yml exec -T airflow-db \
  psql -U airflow -d airflow < airflow_backup_20260112.sql
```

### Backup de DAGs

Los DAGs están en archivos locales en `./airflow/dags/`, simplemente respaldar este directorio.

## Recursos Adicionales

- [Documentación oficial de Airflow](https://airflow.apache.org/docs/)
- [Tutorial de Airflow](https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html)
- [Operadores de Airflow](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/index.html)

## Contacto

Para soporte con Airflow en Boreas RGIOT:
- Email: alonsogpablo@rggestionyenergia.com
