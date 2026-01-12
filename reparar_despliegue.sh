#!/bin/bash
# Script para reparar despliegue - Boreas RGIOT
# Ejecutar en el servidor remoto: bash reparar_despliegue.sh

set -e

echo "=========================================="
echo "REPARACIÓN DE DESPLIEGUE - BOREAS RGIOT"
echo "=========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Detener contenedores
echo -e "${YELLOW}1. Deteniendo contenedores...${NC}"
docker-compose down
echo -e "${GREEN}✓ Contenedores detenidos${NC}"
echo ""

# 2. Limpiar volúmenes de PostgreSQL (CUIDADO: borra BD existente)
echo -e "${YELLOW}2. Limpiando volúmenes de PostgreSQL...${NC}"
echo "   Esto eliminará la base de datos existente."
read -p "   ¿Continuar? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    docker-compose down -v
    echo -e "${GREEN}✓ Volúmenes eliminados${NC}"
else
    echo "   Abortado. Continuar sin limpiar volúmenes."
fi
echo ""

# 3. Iniciar solo base de datos
echo -e "${YELLOW}3. Iniciando PostgreSQL...${NC}"
docker-compose up -d db
echo -e "${GREEN}✓ PostgreSQL iniciado${NC}"
echo ""

# 4. Esperar a que PostgreSQL esté listo
echo -e "${YELLOW}4. Esperando a que PostgreSQL esté listo...${NC}"
sleep 5
for i in {1..30}; do
    if docker-compose exec -T db pg_isready -U postgres &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL está listo${NC}"
        break
    fi
    echo "   Intento $i/30..."
    sleep 2
done
echo ""

# 5. Crear base de datos y usuario
echo -e "${YELLOW}5. Creando base de datos y usuario...${NC}"
docker-compose exec -T db psql -U postgres -c "CREATE DATABASE boreas_db;" 2>/dev/null || echo "   Base de datos ya existe"
docker-compose exec -T db psql -U postgres -c "CREATE USER boreas_user WITH PASSWORD 'boreas_password';" 2>/dev/null || echo "   Usuario ya existe"
docker-compose exec -T db psql -U postgres -c "ALTER ROLE boreas_user CREATEDB;"
docker-compose exec -T db psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE boreas_db TO boreas_user;"
echo -e "${GREEN}✓ Base de datos y usuario creados${NC}"
echo ""

# 6. Iniciar todos los servicios
echo -e "${YELLOW}6. Iniciando todos los servicios...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Servicios iniciados${NC}"
echo ""

# 7. Esperar a que la app esté lista
echo -e "${YELLOW}7. Esperando a que la aplicación esté lista...${NC}"
sleep 10
echo -e "${GREEN}✓ Aplicación debería estar lista${NC}"
echo ""

# 8. Ejecutar migraciones
echo -e "${YELLOW}8. Ejecutando migraciones de Django...${NC}"
docker-compose exec -T web python manage.py migrate
echo -e "${GREEN}✓ Migraciones completadas${NC}"
echo ""

# 9. Cargar fixtures
echo -e "${YELLOW}9. Cargando datos iniciales (fixtures)...${NC}"
docker-compose exec -T web bash -c "python manage.py loaddata fixtures/*.json"
echo -e "${GREEN}✓ Fixtures cargados${NC}"
echo ""

# 10. Recopilar archivos estáticos
echo -e "${YELLOW}10. Recopilando archivos estáticos...${NC}"
docker-compose exec -T web python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ Archivos estáticos recopilados${NC}"
echo ""

# 11. Verificar estado
echo -e "${YELLOW}11. Verificando estado de servicios...${NC}"
docker-compose ps
echo ""

# 12. Verificar logs
echo -e "${YELLOW}12. Verificando logs (últimas 20 líneas)...${NC}"
echo ""
echo "Logs de web:"
docker-compose logs web --tail=20
echo ""
echo "Logs de nginx:"
docker-compose logs nginx --tail=20
echo ""

# 13. Prueba HTTP
echo -e "${YELLOW}13. Probando acceso HTTP...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" == "302" ] || [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Servidor responde (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ Error HTTP $HTTP_CODE${NC}"
    echo "   Ejecutar: docker-compose logs -f"
fi
echo ""

echo "=========================================="
echo "REPARACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo "1. Crear superusuario:"
echo "   docker-compose exec web python manage.py createsuperuser"
echo ""
echo "2. Acceder a:"
echo "   http://tu-servidor/admin/"
echo ""
echo "3. Revisar credenciales MQTT en panel admin"
echo ""
