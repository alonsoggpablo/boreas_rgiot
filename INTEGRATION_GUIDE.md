# Integration Guide: Device Type Mapping & External Device Mapping

## Overview
Two new tables have been created to manage external device integration:
- `boreas_mediacion_device_type_mapping` (16 rows) - Maps external device types to MQTT families
- `boreas_mediacion_external_device_mapping` (25 rows) - Stores complete external device metadata

## Step 1: Add Django Models

Add these models to `boreas_mediacion/models.py`:

```python
# --- External Device Integration ---
class DeviceTypeMapping(models.Model):
    """Maps external device types to internal MQTT device families"""
    external_device_type_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="External device type name (e.g., 'Router', 'Water Meter')"
    )
    mqtt_device_family = models.ForeignKey(
        'MQTT_device_family',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='device_type_mappings',
        help_text="Link to internal MQTT device family"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'boreas_mediacion_device_type_mapping'
        managed = False
        verbose_name = "Device Type Mapping"
        verbose_name_plural = "Device Type Mappings"
        ordering = ['external_device_type_name']

    def __str__(self):
        family = self.mqtt_device_family.name if self.mqtt_device_family else "Unmapped"
        return f"{self.external_device_type_name} → {family}"


class ExternalDeviceMapping(models.Model):
    """Stores external device information with metadata"""
    external_device_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique external device identifier"
    )
    external_alias = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Friendly name for the device"
    )
    internal_device_uuid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="UUID linking to internal system"
    )
    client_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Client/Organization name"
    )
    location_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Physical location"
    )
    group_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Logical grouping"
    )
    purchase_date = models.DateField(
        blank=True,
        null=True,
        help_text="Device acquisition date"
    )
    sale_date = models.DateField(
        blank=True,
        null=True,
        help_text="Device sales/disposal date"
    )
    status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Status: Venta, Stock, etc."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Device is active"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Flexible metadata: device_type, group_name, crawl_date, crawled_from, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'boreas_mediacion_external_device_mapping'
        managed = False
        verbose_name = "External Device Mapping"
        verbose_name_plural = "External Device Mappings"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['external_device_id']),
            models.Index(fields=['client_name']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.external_device_id} ({self.external_alias or 'No alias'})"

    @property
    def device_type(self):
        """Get device type from metadata"""
        return self.metadata.get('device_type', 'Unknown')

    @property
    def crawl_date(self):
        """Get crawl date from metadata"""
        return self.metadata.get('crawl_date')
```

## Step 2: Create Serializers

Add to `boreas_mediacion/serializers.py`:

```python
from .models import DeviceTypeMapping, ExternalDeviceMapping

class DeviceTypeMappingSerializer(serializers.ModelSerializer):
    mqtt_family_name = serializers.CharField(
        source='mqtt_device_family.name',
        read_only=True
    )

    class Meta:
        model = DeviceTypeMapping
        fields = (
            'id',
            'external_device_type_name',
            'mqtt_device_family',
            'mqtt_family_name',
            'created_at'
        )
        read_only_fields = ('created_at',)


class ExternalDeviceMappingSerializer(serializers.ModelSerializer):
    device_type = serializers.CharField(read_only=True)
    crawl_date = serializers.CharField(read_only=True)

    class Meta:
        model = ExternalDeviceMapping
        fields = (
            'id',
            'external_device_id',
            'external_alias',
            'internal_device_uuid',
            'client_name',
            'location_name',
            'group_name',
            'purchase_date',
            'sale_date',
            'status',
            'is_active',
            'device_type',
            'metadata',
            'crawl_date',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')
```

## Step 3: Create ViewSets

Add to `boreas_mediacion/views.py`:

```python
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import DeviceTypeMapping, ExternalDeviceMapping
from .serializers import DeviceTypeMappingSerializer, ExternalDeviceMappingSerializer

class DeviceTypeMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing device type mappings
    
    Endpoints:
    - GET /api/device-types/ - List all mappings
    - POST /api/device-types/ - Create new mapping
    - GET /api/device-types/{id}/ - Retrieve specific mapping
    - PUT /api/device-types/{id}/ - Update mapping
    - DELETE /api/device-types/{id}/ - Delete mapping
    """
    queryset = DeviceTypeMapping.objects.select_related('mqtt_device_family')
    serializer_class = DeviceTypeMappingSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['mqtt_device_family']
    search_fields = ['external_device_type_name']
    ordering_fields = ['external_device_type_name', 'created_at']
    ordering = ['external_device_type_name']


class ExternalDeviceMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing external device mappings
    
    Endpoints:
    - GET /api/external-devices/ - List all devices
    - POST /api/external-devices/ - Create new device
    - GET /api/external-devices/{id}/ - Retrieve specific device
    - PUT /api/external-devices/{id}/ - Update device
    - DELETE /api/external-devices/{id}/ - Delete device
    """
    queryset = ExternalDeviceMapping.objects.all()
    serializer_class = ExternalDeviceMappingSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client_name', 'status', 'is_active']
    search_fields = ['external_device_id', 'external_alias', 'client_name']
    ordering_fields = ['external_device_id', 'client_name', 'updated_at']
    ordering = ['-updated_at']
```

## Step 4: Register URLs

Update `boreas_mediacion/urls.py`:

```python
# In the router registration section:
router.register(r'device-types', views.DeviceTypeMappingViewSet, basename='device-type')
router.register(r'external-devices', views.ExternalDeviceMappingViewSet, basename='external-device')
```

## Step 5: Update Admin Interface

Create/update `boreas_mediacion/admin.py`:

```python
from django.contrib import admin
from .models import DeviceTypeMapping, ExternalDeviceMapping

@admin.register(DeviceTypeMapping)
class DeviceTypeMappingAdmin(admin.ModelAdmin):
    list_display = ('external_device_type_name', 'get_mqtt_family', 'created_at')
    list_filter = ('created_at', 'mqtt_device_family')
    search_fields = ('external_device_type_name',)
    raw_id_fields = ('mqtt_device_family',)
    readonly_fields = ('created_at',)

    def get_mqtt_family(self, obj):
        return obj.mqtt_device_family.name if obj.mqtt_device_family else "—"
    get_mqtt_family.short_description = 'MQTT Family'


@admin.register(ExternalDeviceMapping)
class ExternalDeviceMappingAdmin(admin.ModelAdmin):
    list_display = (
        'external_device_id',
        'external_alias',
        'client_name',
        'device_type_badge',
        'status',
        'is_active_badge',
        'updated_at'
    )
    list_filter = ('status', 'is_active', 'client_name', 'created_at')
    search_fields = ('external_device_id', 'external_alias', 'client_name')
    readonly_fields = ('created_at', 'updated_at', 'metadata_display')
    fieldsets = (
        ('Device Identification', {
            'fields': ('external_device_id', 'external_alias', 'internal_device_uuid')
        }),
        ('Organization', {
            'fields': ('client_name', 'location_name', 'group_name')
        }),
        ('Lifecycle', {
            'fields': ('status', 'purchase_date', 'sale_date', 'is_active')
        }),
        ('Metadata', {
            'fields': ('metadata', 'metadata_display'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def device_type_badge(self, obj):
        device_type = obj.device_type
        colors = {
            'Router': '#007bff',
            'Meter': '#28a745',
            'Punto': '#ffc107',
            'Gateway': '#dc3545',
        }
        color = colors.get(device_type, '#6c757d')
        return f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 3px;">{device_type}</span>'
    device_type_badge.short_description = 'Type'
    device_type_badge.allow_tags = True

    def is_active_badge(self, obj):
        if obj.is_active:
            return '✅ Active'
        return '❌ Inactive'
    is_active_badge.short_description = 'Status'

    def metadata_display(self, obj):
        import json
        return json.dumps(obj.metadata, indent=2, ensure_ascii=False)
    metadata_display.short_description = 'Metadata (JSON)'
```

## Step 6: Create a Management Command (Optional)

Create `boreas_mediacion/management/commands/link_device_types.py`:

```python
from django.core.management.base import BaseCommand
from boreas_mediacion.models import DeviceTypeMapping, MQTT_device_family, ExternalDeviceMapping

class Command(BaseCommand):
    help = 'Link external device types to MQTT device families'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview links without saving')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Define mappings: external_type -> mqtt_family_name
        mappings = {
            'Router': 'routers',
            'Contador Gas': 'gas_meters',
            'DATADIS': 'datadis',
            'Punto': 'wireless',
            'Water Meter': 'water_meters',
        }

        updated = 0
        for external_type, family_name in mappings.items():
            try:
                device_mapping = DeviceTypeMapping.objects.get(external_device_type_name=external_type)
                family = MQTT_device_family.objects.get(name=family_name)

                if not dry_run:
                    device_mapping.mqtt_device_family = family
                    device_mapping.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Linked '{external_type}' → '{family_name}'")
                    )
                else:
                    self.stdout.write(f"[DRY RUN] Would link '{external_type}' → '{family_name}'")
                updated += 1
            except DeviceTypeMapping.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠ Device type '{external_type}' not found"))
            except MQTT_device_family.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠ Family '{family_name}' not found"))

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\n[DRY RUN] Would update {updated} mappings"))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✓ Successfully updated {updated} mappings"))
```

Run with: `python manage.py link_device_types [--dry-run]`

## Step 7: Create Database Migration

```bash
python manage.py makemigrations boreas_mediacion
python manage.py migrate boreas_mediacion
```

**Note:** Since these tables already exist in the DB, use `managed = False` in Meta to prevent Django from trying to create them.

## API Usage Examples

### List all device type mappings
```bash
curl http://localhost:8000/api/device-types/
```

### List external devices by client
```bash
curl "http://localhost:8000/api/external-devices/?client_name=RG%20GEST%C3%8DN"
```

### Search devices by ID
```bash
curl "http://localhost:8000/api/external-devices/?search=COMT241026"
```

### Get device by ID
```bash
curl http://localhost:8000/api/external-devices/1/
```

### Link device type to MQTT family
```bash
curl -X PUT http://localhost:8000/api/device-types/1/ \
  -H "Content-Type: application/json" \
  -d '{"mqtt_device_family": 1}'
```

## Key Features

✅ **Bidirectional Relationships** - Devices linked to families for cross-referencing  
✅ **Flexible Metadata** - JSONB field stores any device attributes  
✅ **Full-Text Search** - Search by ID, alias, or client name  
✅ **Filtering** - Filter by status, client, or active state  
✅ **Audit Trail** - Track creation and modification timestamps  
✅ **Admin Interface** - User-friendly management in Django admin  
✅ **REST API** - Full CRUD operations via REST endpoints  

## Next Steps

1. Test the models with `python manage.py shell`
2. Populate device type mappings via admin or management command
3. Link external devices to internal systems as needed
4. Monitor device status and metadata changes
5. Consider migration script for historical device data
