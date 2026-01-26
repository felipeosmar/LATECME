from django.contrib import admin
from django.utils.html import format_html
from .models import ProductionOrder, Bin, BinHistory, Batch, BatchItem


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'material_code', 'planned_quantity', 'produced_quantity',
        'status', 'responsible', 'planned_start_date', 'planned_end_date',
        'completion_display', 'created_at'
    ]
    list_filter = ['status', 'material__material_type', 'created_at', 'planned_start_date']
    search_fields = ['order_number', 'material__code', 'material__name', 'responsible__username']
    ordering = ['-created_at']
    readonly_fields = [
        'order_number', 'produced_quantity', 'actual_start_date',
        'actual_end_date', 'created_at', 'updated_at'
    ]

    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Material'

    def completion_display(self, obj):
        percentage = obj.completion_percentage
        if percentage >= 100:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, percentage
        )
    completion_display.short_description = '% Conclusão'

    fieldsets = (
        ('Identificação', {
            'fields': ('order_number', 'material', 'status')
        }),
        ('Quantidades', {
            'fields': ('planned_quantity', 'produced_quantity')
        }),
        ('Planejamento', {
            'fields': ('planned_start_date', 'planned_end_date', 'responsible')
        }),
        ('Execução', {
            'fields': ('actual_start_date', 'actual_end_date'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
    )


@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'warehouse_code', 'status', 'current_material_code',
        'current_quantity', 'capacity', 'location_code', 'is_active'
    ]
    list_filter = ['status', 'warehouse', 'is_active']
    search_fields = ['code', 'warehouse__code', 'current_material__code', 'location_code']
    ordering = ['warehouse__code', 'code']

    def warehouse_code(self, obj):
        return obj.warehouse.code
    warehouse_code.short_description = 'Armazém'

    def current_material_code(self, obj):
        if obj.current_material:
            return format_html(
                '<span style="color: blue;">{}</span>',
                obj.current_material.code
            )
        return format_html('<span style="color: gray;">-</span>')
    current_material_code.short_description = 'Material'

    fieldsets = (
        ('Identificação', {
            'fields': ('code', 'warehouse', 'status')
        }),
        ('Capacidade', {
            'fields': ('capacity', 'location_code')
        }),
        ('Conteúdo Atual', {
            'fields': (
                'current_material', 'current_quantity',
                'current_supplier_batch', 'current_certificate'
            )
        }),
        ('Observações', {
            'fields': ('notes', 'is_active')
        }),
    )


@admin.register(BinHistory)
class BinHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'bin_code', 'movement_type', 'material_code',
        'quantity', 'quantity_before', 'quantity_after', 'batch_number', 'performed_by'
    ]
    list_filter = ['movement_type', 'created_at', 'bin__warehouse']
    search_fields = ['bin__code', 'material__code', 'batch__batch_number', 'supplier_batch']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'quantity_before', 'quantity_after']

    def bin_code(self, obj):
        return obj.bin.code
    bin_code.short_description = 'Contentor'

    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Material'

    def batch_number(self, obj):
        if obj.batch:
            return obj.batch.batch_number
        return '-'
    batch_number.short_description = 'Batelada'


class BatchItemInline(admin.TabularInline):
    model = BatchItem
    extra = 0
    readonly_fields = [
        'bin', 'material', 'quantity', 'supplier_batch',
        'certificate', 'collected_by', 'collected_at'
    ]
    can_delete = False


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number', 'production_order_number', 'material_code',
        'status', 'target_quantity', 'actual_quantity', 'quantity_status',
        'prepared_by', 'created_at'
    ]
    list_filter = ['status', 'material__material_type', 'created_at']
    search_fields = ['batch_number', 'production_order__order_number', 'material__code']
    ordering = ['-created_at']
    readonly_fields = [
        'batch_number', 'actual_quantity', 'preparation_date',
        'production_start_date', 'completion_date'
    ]
    inlines = [BatchItemInline]

    def production_order_number(self, obj):
        return obj.production_order.order_number
    production_order_number.short_description = 'Ordem'

    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Material'

    def quantity_status(self, obj):
        variance = obj.quantity_variance
        if obj.is_complete:
            return format_html('<span style="color: green;">Completa</span>')
        elif variance < 0:
            return format_html(
                '<span style="color: orange;">Falta {:.3f} kg</span>',
                abs(variance)
            )
        return format_html('<span style="color: red;">-</span>')
    quantity_status.short_description = 'Status Qtd'

    fieldsets = (
        ('Identificação', {
            'fields': ('batch_number', 'production_order', 'material', 'status')
        }),
        ('Quantidades', {
            'fields': ('target_quantity', 'actual_quantity')
        }),
        ('Execução', {
            'fields': ('prepared_by', 'preparation_date', 'production_start_date', 'completion_date')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
    )


@admin.register(BatchItem)
class BatchItemAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number', 'bin_code', 'material_code', 'quantity',
        'supplier_batch', 'certificate', 'collected_by', 'collected_at'
    ]
    list_filter = ['batch__status', 'collected_at']
    search_fields = ['batch__batch_number', 'bin__code', 'material__code', 'supplier_batch']
    ordering = ['-collected_at']

    def batch_number(self, obj):
        return obj.batch.batch_number
    batch_number.short_description = 'Batelada'

    def bin_code(self, obj):
        if obj.bin:
            return obj.bin.code
        return '-'
    bin_code.short_description = 'Contentor'

    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Material'
