#!/bin/bash
# Script para cargar fixtures iniciales en el despliegue de Boreas RGIOT
# Este script debe ejecutarse DESPUÉS de las migraciones y ANTES de crear el superusuario

set -e  # Detener en caso de error

echo "========================================="
echo "Cargando datos iniciales (fixtures)"
echo "========================================="
echo ""

FIXTURES_DIR="/app/fixtures"

if [ ! -d "$FIXTURES_DIR" ]; then
    echo "❌ Error: Directorio de fixtures no encontrado: $FIXTURES_DIR"
    exit 1
fi

# Contar fixtures disponibles
FIXTURE_COUNT=$(ls -1 $FIXTURES_DIR/*.json 2>/dev/null | wc -l)

if [ "$FIXTURE_COUNT" -eq 0 ]; then
    echo "❌ Error: No se encontraron archivos de fixtures en $FIXTURES_DIR"
    exit 1
fi

echo "📦 Encontrados $FIXTURE_COUNT archivos de fixtures"
echo ""

# Cargar fixtures en orden
for fixture in $FIXTURES_DIR/*.json; do
    fixture_name=$(basename "$fixture")
    echo "⏳ Cargando: $fixture_name"
    
    if python manage.py loaddata "$fixture"; then
        echo "✓ $fixture_name cargado correctamente"
    else
        echo "❌ Error cargando: $fixture_name"
        exit 1
    fi
    echo ""
done

echo "========================================="
echo "✅ Todos los fixtures cargados exitosamente"
echo "========================================="
echo ""
echo "Datos cargados:"
echo "  - Familias de dispositivos MQTT"
echo "  - Brokers MQTT"
echo "  - Topics MQTT"
echo "  - Tipos de actuaciones de sensores"
echo "  - Parámetros de router"
echo ""
echo "⚠️  IMPORTANTE: Revisar y actualizar credenciales de brokers MQTT"
echo "   en el panel de administración antes de usar en producción."
echo ""
