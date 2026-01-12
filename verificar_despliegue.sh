#!/bin/bash
# Script de verificación del despliegue de Boreas RGIOT
# Ejecutar en el servidor remoto: bash verificar_despliegue.sh

echo "=========================================="
echo "VERIFICACIÓN DE DESPLIEGUE - BOREAS RGIOT"
echo "=========================================="
echo ""

# 1. Verificar que Docker está instalado
echo "1. Verificando Docker..."
if command -v docker &> /dev/null; then
    echo "   ✓ Docker instalado: $(docker --version)"
else
    echo "   ✗ Docker NO está instalado"
    exit 1
fi
echo ""

# 2. Verificar que Docker Compose está instalado
echo "2. Verificando Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "   ✓ Docker Compose instalado: $(docker-compose --version)"
else
    echo "   ✗ Docker Compose NO está instalado"
    exit 1
fi
echo ""

# 3. Verificar contenedores en ejecución
echo "3. Verificando contenedores activos..."
CONTAINERS=$(docker-compose ps --services --filter "status=running" 2>/dev/null | wc -l)
echo "   Contenedores principales:"
docker-compose ps
echo ""

if [ "$CONTAINERS" -ge 3 ]; then
    echo "   ✓ Contenedores principales corriendo ($CONTAINERS/3)"
else
    echo "   ⚠ Solo $CONTAINERS contenedores corriendo (esperados: 3)"
fi
echo ""

# 4. Verificar estado de la base de datos
echo "4. Verificando base de datos PostgreSQL..."
if docker-compose exec -T db pg_isready -U boreas_user &> /dev/null; then
    echo "   ✓ PostgreSQL está listo y aceptando conexiones"
else
    echo "   ✗ PostgreSQL NO está respondiendo"
fi
echo ""

# 5. Verificar migraciones de Django
echo "5. Verificando migraciones de Django..."
MIGRATIONS=$(docker-compose exec -T web python manage.py showmigrations --plan 2>/dev/null | grep -c "\[X\]")
PENDING=$(docker-compose exec -T web python manage.py showmigrations --plan 2>/dev/null | grep -c "\[ \]")
echo "   Migraciones aplicadas: $MIGRATIONS"
echo "   Migraciones pendientes: $PENDING"

if [ "$PENDING" -eq 0 ]; then
    echo "   ✓ Todas las migraciones aplicadas"
else
    echo "   ⚠ Hay $PENDING migraciones pendientes"
fi
echo ""

# 6. Verificar archivos estáticos
echo "6. Verificando archivos estáticos..."
STATIC_FILES=$(docker-compose exec -T web ls -1 /app/staticfiles 2>/dev/null | wc -l)
if [ "$STATIC_FILES" -gt 0 ]; then
    echo "   ✓ Archivos estáticos recopilados ($STATIC_FILES carpetas/archivos)"
else
    echo "   ⚠ No se encontraron archivos estáticos"
fi
echo ""

# 7. Verificar acceso HTTP
echo "7. Verificando acceso HTTP..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/ 2>/dev/null)
if [ "$HTTP_CODE" == "302" ] || [ "$HTTP_CODE" == "200" ]; then
    echo "   ✓ Servidor web responde (HTTP $HTTP_CODE)"
else
    echo "   ⚠ Servidor web no responde correctamente (HTTP $HTTP_CODE)"
fi
echo ""

# 8. Verificar logs recientes de errores
echo "8. Verificando errores recientes en logs..."
ERRORS=$(docker-compose logs --tail=100 web 2>/dev/null | grep -i "error\|exception\|critical" | wc -l)
if [ "$ERRORS" -eq 0 ]; then
    echo "   ✓ No se encontraron errores en logs recientes"
else
    echo "   ⚠ Se encontraron $ERRORS líneas con errores en logs"
    echo "   Ejecuta: docker-compose logs web --tail=50"
fi
echo ""

# 9. Verificar puertos en uso
echo "9. Verificando puertos..."
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo "   ✓ Puerto 80 (HTTP) en uso"
else
    echo "   ⚠ Puerto 80 no está en uso"
fi

if netstat -tlnp 2>/dev/null | grep -q ":5432 "; then
    echo "   ✓ Puerto 5432 (PostgreSQL) en uso"
else
    echo "   ⚠ Puerto 5432 no está en uso"
fi
echo ""

# 10. Verificar uso de recursos
echo "10. Verificando uso de recursos..."
echo "    Contenedores y recursos:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""

# 11. Verificar Airflow (opcional)
echo "11. Verificando Airflow (opcional)..."
AIRFLOW_CONTAINERS=$(docker-compose -f docker-compose.airflow.yml ps --services --filter "status=running" 2>/dev/null | wc -l)
if [ "$AIRFLOW_CONTAINERS" -gt 0 ]; then
    echo "   ✓ Airflow desplegado ($AIRFLOW_CONTAINERS contenedores)"
    docker-compose -f docker-compose.airflow.yml ps
else
    echo "   - Airflow no está desplegado (opcional)"
fi
echo ""

# Resumen final
echo "=========================================="
echo "RESUMEN DE VERIFICACIÓN"
echo "=========================================="

# Contador de verificaciones exitosas
CHECKS=0
TOTAL=8

command -v docker &> /dev/null && ((CHECKS++))
command -v docker-compose &> /dev/null && ((CHECKS++))
[ "$CONTAINERS" -ge 3 ] && ((CHECKS++))
docker-compose exec -T db pg_isready -U boreas_user &> /dev/null && ((CHECKS++))
[ "$PENDING" -eq 0 ] && ((CHECKS++))
[ "$STATIC_FILES" -gt 0 ] && ((CHECKS++))
[ "$HTTP_CODE" == "302" ] || [ "$HTTP_CODE" == "200" ] && ((CHECKS++))
[ "$ERRORS" -eq 0 ] && ((CHECKS++))

echo "Verificaciones exitosas: $CHECKS/$TOTAL"
echo ""

if [ "$CHECKS" -eq "$TOTAL" ]; then
    echo "✓ SISTEMA FUNCIONANDO CORRECTAMENTE"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Acceder a http://tu-servidor/admin/"
    echo "  2. Verificar fixtures cargados (Device Families, Brokers, Topics)"
    echo "  3. Configurar credenciales MQTT en el panel admin"
    exit 0
elif [ "$CHECKS" -ge 5 ]; then
    echo "⚠ SISTEMA PARCIALMENTE FUNCIONAL"
    echo ""
    echo "Revisar logs para más detalles:"
    echo "  docker-compose logs -f"
    exit 1
else
    echo "✗ SISTEMA CON PROBLEMAS"
    echo ""
    echo "Comandos para diagnóstico:"
    echo "  docker-compose ps"
    echo "  docker-compose logs -f"
    echo "  docker-compose down && docker-compose up -d"
    exit 2
fi
