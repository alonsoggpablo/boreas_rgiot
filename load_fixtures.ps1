# Script PowerShell para cargar fixtures iniciales en el despliegue de Boreas RGIOT
# Este script debe ejecutarse DESPUÉS de las migraciones y ANTES de crear el superusuario

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Cargando datos iniciales (fixtures)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectDir = "c:\Users\Usuario\Documents\GitHub\boreas_rgiot"
$FixturesDir = Join-Path $ProjectDir "boreas_mediacion\fixtures"

if (-not (Test-Path $FixturesDir)) {
    Write-Host "❌ Error: Directorio de fixtures no encontrado: $FixturesDir" -ForegroundColor Red
    exit 1
}

# Obtener todos los archivos JSON
$Fixtures = Get-ChildItem -Path $FixturesDir -Filter "*.json" | Sort-Object Name

if ($Fixtures.Count -eq 0) {
    Write-Host "❌ Error: No se encontraron archivos de fixtures en $FixturesDir" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Encontrados $($Fixtures.Count) archivos de fixtures" -ForegroundColor Yellow
Write-Host ""

# Cargar cada fixture
foreach ($fixture in $Fixtures) {
    Write-Host "⏳ Cargando: $($fixture.Name)" -ForegroundColor Yellow
    
    try {
        docker compose exec web python manage.py loaddata "fixtures/$($fixture.Name)"
        Write-Host "✓ $($fixture.Name) cargado correctamente" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error cargando: $($fixture.Name)" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

Write-Host "=========================================" -ForegroundColor Green
Write-Host "✅ Todos los fixtures cargados exitosamente" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Datos cargados:" -ForegroundColor Cyan
Write-Host "  - Familias de dispositivos MQTT"
Write-Host "  - Brokers MQTT"
Write-Host "  - Topics MQTT"
Write-Host "  - Tipos de actuaciones de sensores"
Write-Host "  - Parámetros de router"
Write-Host ""
Write-Host "⚠️  IMPORTANTE: Revisar y actualizar credenciales de brokers MQTT" -ForegroundColor Yellow
Write-Host "   en el panel de administración antes de usar en producción." -ForegroundColor Yellow
Write-Host ""
