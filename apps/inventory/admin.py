from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Warehouse, MaterialStock, StockMovement,
    StockReservation, InventoryCount, InventoryCountItem
)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'location', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'location', 'manager__username']
    ordering = ['code']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('code', 'name', 'description')
        }),
        ('Localização', {
            'fields': ('location', 'manager')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(MaterialStock)
class MaterialStockAdmin(admin.ModelAdmin):
    list_display = [
        'material_code', 'warehouse_code', 'current_quantity',
        'reserved_quantity', 'available_quantity_display', 'stock_status',
        'last_movement_date'
    ]
    list_filter = ['warehouse', 'material__material_type', 'last_movement_date']
    search_fields = ['material__code', 'material__name', 'warehouse__code']
    ordering = ['material__code', 'warehouse__code']
    readonly_fields = ['last_movement_date']

    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Material'

    def warehouse_code(self, obj):
        return obj.warehouse.code
    warehouse_code.short_description = 'Armazém'

    def available_quantity_display(self, obj):
        return f"{obj.available_quantity:.3f} kg"
    available_quantity_display.short_description = 'Disponível'

    def stock_status(self, obj):
        if obj.is_out_of_stock:
            return format_html('<span style="color: red;">Sem Estoque</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange;">Estoque Baixo</span>')
        else:
            return format_html('<span style="color: green;">Normal</span>')
    stock_status.short_description = 'Status'

    fieldsets = (
        ('Material e Armazém', {
            'fields': ('material', 'warehouse', 'location_code')
        }),
        ('Quantidades', {
            'fields': ('current_quantity', 'reserved_quantity', 'minimum_stock', 'maximum_stock')
        }),
        ('Informações', {
            'fields': ('last_movement_date',)
        }),
    )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'material_code', 'warehouse_code',
        'movement_type', 'quantity', 'reason', 'user',
        'reference_document'
    ]
    list_filter = [
        'movement_type', 'reason', 'created_at',
        'warehouse', 'material__material_type'
    ]
    search_fields = [
        'material__code', 'material__name', 'warehouse__code',
        'reference_document', 'batch_number'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Material'

    def warehouse_code(self, obj):
        return obj.warehouse.code
    warehouse_code.short_description = 'Armazém'

    fieldsets = (
        ('Movimentação', {
            'fields': ('material', 'warehouse', 'movement_type', 'reason')
        }),
        ('Quantidade e Custo', {
            'fields': ('quantity', 'unit_cost', 'total_cost')
        }),
        ('Informações do Lote', {
            'fields': ('batch_number', 'expiry_date', 'certificate_number')
        }),
        ('Referências', {
            'fields': ('reference_document', 'destination_warehouse', 'user')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['material', 'warehouse', 'movement_type', 'quantity']
        return self.readonly_fields


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = [
        'material_code', 'warehouse_code', 'quantity',
        'reserved_by', 'reservation_date', 'expiry_date',
        'status_display', 'purpose'
    ]
    list_filter = ['reservation_date', 'expiry_date', 'warehouse', 'reserved_by']
    search_fields = [
        'material__code', 'material__name', 'warehouse__code',
        'reserved_by__username', 'purpose'
    ]
    ordering = ['-reservation_date']

    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Material'

    def warehouse_code(self, obj):
        return obj.warehouse.code
    warehouse_code.short_description = 'Armazém'

    def status_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expirado</span>')
        else:
            return format_html('<span style="color: green;">Ativo</span>')
    status_display.short_description = 'Status'

    fieldsets = (
        ('Reserva', {
            'fields': ('material', 'warehouse', 'quantity')
        }),
        ('Responsável', {
            'fields': ('reserved_by', 'purpose')
        }),
        ('Datas', {
            'fields': ('reservation_date', 'expiry_date')
        }),
        ('Referências', {
            'fields': ('reference_document', 'notes')
        }),
    )


class InventoryCountItemInline(admin.TabularInline):
    model = InventoryCountItem
    extra = 0
    readonly_fields = ['system_quantity', 'variance_display']

    def variance_display(self, obj):
        if obj.variance is not None:
            if obj.variance > 0:
                return format_html(
                    '<span style="color: green;">+{:.3f} kg</span>',
                    obj.variance
                )
            elif obj.variance < 0:
                return format_html(
                    '<span style="color: red;">{:.3f} kg</span>',
                    obj.variance
                )
            else:
                return format_html('<span style="color: blue;">0.000 kg</span>')
        return '-'
    variance_display.short_description = 'Variação'


@admin.register(InventoryCount)
class InventoryCountAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'warehouse', 'count_date',
        'status', 'counter', 'supervisor'
    ]
    list_filter = ['status', 'count_date', 'warehouse']
    search_fields = ['reference_number', 'warehouse__code', 'counter__username']
    ordering = ['-count_date']
    inlines = [InventoryCountItemInline]

    fieldsets = (
        ('Contagem', {
            'fields': ('reference_number', 'warehouse', 'count_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Responsáveis', {
            'fields': ('counter', 'supervisor')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == 'COMPLETED':
            return ['reference_number', 'warehouse', 'count_date']
        return ['reference_number']


@admin.register(InventoryCountItem)
class InventoryCountItemAdmin(admin.ModelAdmin):
    list_display = [
        'inventory_count', 'material_code', 'system_quantity',
        'counted_quantity', 'variance_display', 'location_code'
    ]
    list_filter = ['inventory_count__status', 'inventory_count__count_date']
    search_fields = ['material__code', 'inventory_count__reference_number']
    ordering = ['inventory_count', 'material__code']

    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Material'

    def variance_display(self, obj):
        if obj.variance is not None:
            if obj.variance > 0:
                return format_html(
                    '<span style="color: green;">+{:.3f} kg</span>',
                    obj.variance
                )
            elif obj.variance < 0:
                return format_html(
                    '<span style="color: red;">{:.3f} kg</span>',
                    obj.variance
                )
            else:
                return format_html('<span style="color: blue;">0.000 kg</span>')
        return '-'
    variance_display.short_description = 'Variação'
