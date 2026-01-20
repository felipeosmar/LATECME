# Sistema de Controle de Manufatura - Arquitetura Django

## 1. Stack Tecnológica Definida

- **Framework**: Django 4.2 LTS
- **API**: Django REST Framework (DRF) 3.14
- **Documentação API**: drf-spectacular (Swagger/OpenAPI)
- **Tarefas Assíncronas**: Celery 5.3 + Redis
- **Banco de Dados**: PostgreSQL 14+
- **Cache/Broker**: Redis 7+
- **Autenticação**: Django + JWT (djangorestframework-simplejwt)

## 2. Estrutura do Projeto Django

```
manufatura/
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── __init__.py
│   ├── core/               # App base com modelos compartilhados
│   │   ├── models.py
│   │   ├── admin.py
│   │   └── utils.py
│   ├── identification/     # Sistema de códigos únicos
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── api/
│   │   │   ├── serializers.py
│   │   │   └── views.py
│   │   ├── services.py
│   │   └── tasks.py
│   ├── materials/         # Cadastro de ligas
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── api/
│   │   └── services.py
│   ├── inventory/         # Controle de estoque
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── api/
│   │   ├── services.py
│   │   └── tasks.py
│   ├── purchasing/        # Compras
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── api/
│   │   └── services.py
│   └── hardware/          # Interface com hardware
│       ├── services.py
│       ├── tasks.py
│       └── utils.py
├── static/
├── media/
├── templates/
│   └── admin/            # Customização do admin
├── locale/               # Tradução pt-BR
└── tests/
```

## 3. Configuração Base do Django

### 3.1 Settings Base (config/settings/base.py)

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'corsheaders',
    'django_filters',
]

LOCAL_APPS = [
    'apps.core',
    'apps.identification',
    'apps.materials',
    'apps.inventory',
    'apps.purchasing',
    'apps.hardware',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'manufatura'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
    }
}

# Swagger/OpenAPI
SPECTACULAR_SETTINGS = {
    'TITLE': 'Sistema de Manufatura API',
    'DESCRIPTION': 'API para controle de estoque e produção',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

### 3.2 Configuração do Celery (config/celery.py)

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('manufatura')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configurações de filas específicas
app.conf.task_routes = {
    'apps.hardware.tasks.*': {'queue': 'hardware'},
    'apps.inventory.tasks.*': {'queue': 'inventory'},
    'apps.identification.tasks.*': {'queue': 'printing'},
}
```

## 4. Implementação dos Módulos

### 4.1 Módulo Core - Base Models (apps/core/models.py)

```python
from django.db import models
from django.contrib.auth.models import User
import uuid

class TimeStampedModel(models.Model):
    """Modelo abstrato com campos de timestamp"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class BaseModel(TimeStampedModel):
    """Modelo base com UUID e campos de auditoria"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        null=True
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='%(class)s_updated',
        null=True
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
```

### 4.2 Módulo Materials (apps/materials/models.py)

```python
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel

class Supplier(BaseModel):
    """Fornecedores de materiais"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    cnpj = models.CharField(max_length=18, unique=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Material(BaseModel):
    """Ligas metálicas para manufatura"""
    MATERIAL_TYPES = [
        ('AL', 'Alumínio'),
        ('TI', 'Titânio'),
        ('SS', 'Aço Inox'),
        ('IN', 'Inconel'),
        ('CO', 'Cobalto-Cromo'),
    ]
    
    code = models.CharField(
        max_length=10, 
        unique=True,
        help_text="Código interno (ex: AL7075, TI6AL4V)"
    )
    name = models.CharField(max_length=200)
    material_type = models.CharField(max_length=2, choices=MATERIAL_TYPES)
    composition = models.JSONField(
        default=dict,
        help_text="Composição química {elemento: percentual}"
    )
    density = models.DecimalField(
        max_digits=5, 
        decimal_places=3,
        validators=[MinValueValidator(0.1), MaxValueValidator(20.0)],
        help_text="Densidade em g/cm³"
    )
    suppliers = models.ManyToManyField(
        Supplier,
        through='MaterialSupplier',
        related_name='materials'
    )
    specifications = models.JSONField(default=dict)
    requires_certificate = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class MaterialSupplier(BaseModel):
    """Relação Material-Fornecedor com preço"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    supplier_code = models.CharField(max_length=100)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=3)
    lead_time_days = models.IntegerField()
    
    class Meta:
        unique_together = ['material', 'supplier']
        verbose_name = "Material-Fornecedor"
```

### 4.3 Admin Customizado (apps/materials/admin.py)

```python
from django.contrib import admin
from django.utils.html import format_html
from .models import Material, Supplier, MaterialSupplier

class MaterialSupplierInline(admin.TabularInline):
    model = MaterialSupplier
    extra = 1

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'material_type', 'density', 'supplier_count']
    list_filter = ['material_type', 'requires_certificate']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [MaterialSupplierInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('code', 'name', 'material_type')
        }),
        ('Propriedades', {
            'fields': ('density', 'composition', 'specifications')
        }),
        ('Controle', {
            'fields': ('requires_certificate', 'is_active')
        }),
        ('Auditoria', {
            'classes': ('collapse',),
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by')
        }),
    )
    
    def supplier_count(self, obj):
        count = obj.suppliers.count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 0 else 'red',
            count
        )
    supplier_count.short_description = 'Fornecedores'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
```

### 4.4 API com DRF (apps/materials/api/serializers.py)

```python
from rest_framework import serializers
from apps.materials.models import Material, Supplier, MaterialSupplier

class MaterialSupplierSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = MaterialSupplier
        fields = [
            'supplier', 'supplier_name', 'supplier_code',
            'price_per_kg', 'minimum_order', 'lead_time_days'
        ]

class MaterialSerializer(serializers.ModelSerializer):
    suppliers_detail = MaterialSupplierSerializer(
        source='materialsupplier_set', 
        many=True, 
        read_only=True
    )
    
    class Meta:
        model = Material
        fields = [
            'id', 'code', 'name', 'material_type',
            'density', 'composition', 'specifications',
            'requires_certificate', 'suppliers_detail'
        ]
        read_only_fields = ['id']
    
    def validate_code(self, value):
        """Valida formato do código do material"""
        import re
        if not re.match(r'^(AL|TI|SS|IN|CO)\d{4}$', value):
            raise serializers.ValidationError(
                "Código deve seguir o padrão: TIPO + 4 dígitos (ex: AL7075)"
            )
        return value
```

### 4.5 Views da API (apps/materials/api/views.py)

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema

from apps.materials.models import Material
from .serializers import MaterialSerializer

class MaterialFilter(filters.FilterSet):
    material_type = filters.ChoiceFilter(choices=Material.MATERIAL_TYPES)
    has_certificate = filters.BooleanFilter(field_name='requires_certificate')
    min_density = filters.NumberFilter(field_name='density', lookup_expr='gte')
    max_density = filters.NumberFilter(field_name='density', lookup_expr='lte')
    
    class Meta:
        model = Material
        fields = ['material_type', 'requires_certificate']

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.filter(is_active=True)
    serializer_class = MaterialSerializer
    filterset_class = MaterialFilter
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'created_at']
    
    @extend_schema(
        description="Verifica disponibilidade de um material em estoque"
    )
    @action(detail=True, methods=['get'])
    def check_availability(self, request, pk=None):
        material = self.get_object()
        # Aqui integraria com o módulo de inventory
        return Response({
            'material': material.code,
            'available_kg': 150.5,  # Placeholder
            'reserved_kg': 25.0,
            'locations': ['A1', 'A2']
        })
```

### 4.6 Integração com Celery (apps/hardware/tasks.py)

```python
from celery import shared_task
from django.core.cache import cache
import time

@shared_task(bind=True, max_retries=3)
def print_label_task(self, unique_code, material_info):
    """
    Tarefa assíncrona para impressão de etiquetas
    Não bloqueia a requisição HTTP
    """
    try:
        from apps.hardware.services import LabelPrinterService
        
        printer = LabelPrinterService()
        
        # Prepara dados da etiqueta
        label_data = {
            'code': unique_code,
            'material': material_info['code'],
            'weight': material_info['weight'],
            'date': material_info['entry_date']
        }
        
        # Imprime (operação que pode demorar)
        result = printer.print_barcode_label(label_data)
        
        # Atualiza status no cache
        cache.set(f'print_job:{unique_code}', 'completed', 300)
        
        return {
            'status': 'success',
            'code': unique_code,
            'printed_at': time.time()
        }
        
    except Exception as exc:
        # Retry com backoff exponencial
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

@shared_task
def read_barcode_continuous():
    """
    Leitura contínua de código de barras
    Envia para websocket via channels
    """
    from apps.hardware.services import BarcodeReaderService
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    reader = BarcodeReaderService()
    
    for code in reader.read_stream():
        # Envia para websocket
        async_to_sync(channel_layer.group_send)(
            "barcode_readers",
            {
                "type": "barcode_message",
                "code": code,
                "timestamp": time.time()
            }
        )
```

### 4.7 URLs Configuration (config/urls.py)

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    path('api/v1/', include([
        path('materials/', include('apps.materials.api.urls')),
        path('inventory/', include('apps.inventory.api.urls')),
        path('identification/', include('apps.identification.api.urls')),
        path('purchasing/', include('apps.purchasing.api.urls')),
    ])),
]

# Customização do Admin
admin.site.site_header = "Sistema de Manufatura Aditiva"
admin.site.site_title = "Manufatura Admin"
admin.site.index_title = "Painel de Controle"
```

## 5. Comandos de Desenvolvimento

### 5.1 Setup Inicial

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements/development.txt

# Configurar banco de dados
createdb manufatura

# Executar migrações
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic

# Iniciar Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Iniciar Celery Worker
celery -A config worker -l info

# Iniciar Celery Beat (agendador)
celery -A config beat -l info

# Iniciar servidor de desenvolvimento
python manage.py runserver
```

### 5.2 Comandos Customizados

```python
# apps/inventory/management/commands/generate_test_data.py
from django.core.management.base import BaseCommand
from apps.materials.models import Material
from apps.inventory.models import StockItem

class Command(BaseCommand):
    help = 'Gera dados de teste para desenvolvimento'
    
    def handle(self, *args, **options):
        # Criar materiais de teste
        materials = [
            {'code': 'AL7075', 'name': 'Alumínio 7075', 'type': 'AL', 'density': 2.81},
            {'code': 'TI6AL4', 'name': 'Titânio Grade 5', 'type': 'TI', 'density': 4.43},
        ]
        
        for mat_data in materials:
            Material.objects.get_or_create(
                code=mat_data['code'],
                defaults={
                    'name': mat_data['name'],
                    'material_type': mat_data['type'],
                    'density': mat_data['density']
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Dados de teste criados!'))
```

## 6. Próximos Passos

Com a arquitetura Django definida, podemos implementar os módulos na seguinte ordem:

1. **Módulo Identification** - Sistema de códigos únicos
2. **Módulo Inventory** - Entrada e saída de materiais
3. **Integração Hardware** - Impressora e leitor
4. **Módulo Purchasing** - Pedidos de compra

Qual módulo você gostaria de implementar primeiro? Posso detalhar:
- Models completos
- Admin interface customizada
- API endpoints
- Tarefas Celery
- Testes unitários