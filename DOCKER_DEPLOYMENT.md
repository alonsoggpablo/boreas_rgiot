# INSTRUCCIONES DE DESPLIEGUE CON DOCKER

## Requisitos
- Docker
- Docker Compose

## Pasos para desplegar

### 1. Preparar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus valores específicos
```

### 2. Actualizar requirements.txt (opcional)
Asegúrate de que `gunicorn` esté en requirements.txt para producción:
```bash
echo "gunicorn==20.1.0" >> requirements.txt
```

### 3. Actualizar settings.py de Django
Asegúrate de que tu archivo `boreas_mediacion/settings.py` incluya:

```python
import os
from pathlib import Path

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Base de datos
if os.getenv('DATABASE_URL'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY')
```

### 4. Construir e iniciar los contenedores
```bash
docker-compose up -d
```

### 5. Verificar que todo funcione
```bash
# Ver logs
docker-compose logs -f web

# Ejecutar migraciones (se ejecutan automáticamente)
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Acceder a la aplicación
http://localhost:8000
```

### 6. Detener contenedores
```bash
docker-compose down
```

## Comandos útiles

```bash
# Ver estado de los servicios
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f web

# Ejecutar comando en el contenedor
docker-compose exec web python manage.py <comando>

# Entrar a la consola del contenedor
docker-compose exec web bash

# Conectar a la base de datos PostgreSQL
docker-compose exec db psql -U boreas_user -d boreas_db

# Limpiar volúmenes y contenedores (CUIDADO: Borra datos)
docker-compose down -v
```

## Configuración de producción

Para producción, modifica el archivo `docker-compose.yml`:

1. Usa una imagen base más pequeña (Alpine)
2. Aumenta el número de workers en gunicorn según CPUs disponibles
3. Configura un proxy inverso (nginx)
4. Usa variables de entorno seguras
5. Configura HTTPS/SSL
6. Usa una base de datos externa en producción

## Dockerfile Avanzado (Multietapa - Opcional)

Para reducir tamaño de imagen, puedes usar multietapas. Consulta la documentación de Docker.
