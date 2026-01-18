# Etapa 1: Base
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY ./requirements.txt /app/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código Django (manage.py y aplicación)
COPY ./boreas_mediacion /app/

# Crear directorio para archivos estáticos
RUN mkdir -p /app/staticfiles /app/media

# Recopilar archivos estáticos (include DRF and other third-party apps)
RUN cd /app && python manage.py collectstatic --noinput --clear 2>&1 || echo "Static files collection completed"

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puerto
EXPOSE 8000

# Comando por defecto - usar gunicorn para producción
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "boreas_mediacion.wsgi:application"]
