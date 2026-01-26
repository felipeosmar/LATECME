from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import LabelTemplate, PrinterConfiguration, PrintJob


@admin.register(LabelTemplate)
class LabelTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'dimensions', 'printer_dpi', 'is_default', 'created_at']
    list_filter = ['is_default', 'printer_dpi', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'width_dots', 'height_dots']

    fieldsets = [
        ('Informações Básicas', {
            'fields': ['name', 'description', 'is_default']
        }),
        ('Dimensões', {
            'fields': [
                ('width_mm', 'height_mm'),
                'printer_dpi',
                ('width_dots', 'height_dots'),
            ]
        }),
        ('Configuração', {
            'fields': ['template_json'],
            'classes': ['collapse']
        }),
        ('Auditoria', {
            'fields': [
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            ],
            'classes': ['collapse']
        }),
    ]

    def dimensions(self, obj):
        return f"{obj.width_mm}x{obj.height_mm}mm"
    dimensions.short_description = 'Dimensões'

    def save_model(self, request, obj, form, change):
        if not change:  # Novo objeto
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PrinterConfiguration)
class PrinterConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'connection_info', 'status_indicator', 'is_default', 'last_test_date']
    list_filter = ['is_default', 'last_test_success', 'created_at']
    search_fields = ['name', 'ip_address']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'last_test_date', 'last_test_success']

    fieldsets = [
        ('Informações Básicas', {
            'fields': ['name', 'is_default']
        }),
        ('Conexão', {
            'fields': [
                'ip_address',
                'port',
                'timeout_seconds',
            ]
        }),
        ('Configurações', {
            'fields': ['default_warehouse']
        }),
        ('Status de Conexão', {
            'fields': ['last_test_date', 'last_test_success'],
            'classes': ['collapse']
        }),
        ('Auditoria', {
            'fields': [
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            ],
            'classes': ['collapse']
        }),
    ]

    def status_indicator(self, obj):
        if obj.last_test_success is None:
            return mark_safe('<span style="color: gray;">⚫ Não testado</span>')
        elif obj.last_test_success:
            return mark_safe('<span style="color: green;">✓ Online</span>')
        else:
            return mark_safe('<span style="color: red;">✗ Offline</span>')
    status_indicator.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        if not change:  # Novo objeto
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'bin_code', 'printer', 'template', 'status', 'printed_at']
    list_filter = ['status', 'printer', 'created_at', 'printed_at']
    search_fields = ['bin__code', 'printer__name', 'template__name']
    readonly_fields = [
        'printer', 'template', 'bin', 'status',
        'epl_content', 'bin_data_snapshot',
        'printed_at', 'error_message',
        'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    date_hierarchy = 'created_at'

    fieldsets = [
        ('Trabalho de Impressão', {
            'fields': ['status', 'printer', 'template', 'bin']
        }),
        ('Resultado', {
            'fields': ['printed_at', 'error_message']
        }),
        ('Comandos EPL', {
            'fields': ['epl_content'],
            'classes': ['collapse']
        }),
        ('Snapshot dos Dados', {
            'fields': ['bin_data_snapshot'],
            'classes': ['collapse']
        }),
        ('Auditoria', {
            'fields': [
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            ],
            'classes': ['collapse']
        }),
    ]

    def has_add_permission(self, request):
        # Não permitir adição manual de print jobs via admin
        return False

    def has_delete_permission(self, request, obj=None):
        # Apenas superusers podem deletar print jobs
        return request.user.is_superuser
