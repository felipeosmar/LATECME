from django.contrib import admin
from django.utils import timezone

from .models import (
    PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    Receiving, ReceivingItem
)


class PurchaseRequestItemInline(admin.TabularInline):
    model = PurchaseRequestItem
    extra = 1
    fields = ('material', 'quantity', 'estimated_unit_price', 'preferred_supplier', 'notes')
    autocomplete_fields = ['material', 'preferred_supplier']


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number', 'status', 'priority', 'requester',
        'warehouse', 'request_date', 'required_date', 'total_value_display'
    )
    list_filter = ('status', 'priority', 'warehouse', 'request_date')
    search_fields = ('reference_number', 'requester__username', 'requester__email', 'justification')
    readonly_fields = ('reference_number', 'created_at', 'updated_at', 'created_by', 'updated_by')
    autocomplete_fields = ['requester', 'warehouse', 'approved_by']
    date_hierarchy = 'request_date'
    inlines = [PurchaseRequestItemInline]

    fieldsets = (
        ('Informacoes Basicas', {
            'fields': ('reference_number', 'status', 'priority', 'requester', 'department')
        }),
        ('Detalhes', {
            'fields': ('warehouse', 'request_date', 'required_date', 'justification', 'notes')
        }),
        ('Aprovacao', {
            'fields': ('approved_by', 'approved_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_requests', 'reject_requests']

    def total_value_display(self, obj):
        return f"R$ {obj.total_value:,.2f}"
    total_value_display.short_description = "Valor Total"

    @admin.action(description="Aprovar solicitacoes selecionadas")
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f"{updated} solicitacao(oes) aprovada(s).")

    @admin.action(description="Rejeitar solicitacoes selecionadas")
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='REJECTED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f"{updated} solicitacao(oes) rejeitada(s).")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ('material', 'quantity', 'unit_price', 'received_quantity', 'notes')
    readonly_fields = ('received_quantity',)
    autocomplete_fields = ['material']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number', 'status', 'supplier', 'warehouse',
        'order_date', 'expected_delivery_date', 'total_value_display'
    )
    list_filter = ('status', 'supplier', 'warehouse', 'order_date')
    search_fields = ('reference_number', 'supplier__trade_name', 'supplier__legal_name')
    readonly_fields = ('reference_number', 'created_at', 'updated_at', 'created_by', 'updated_by')
    autocomplete_fields = ['supplier', 'warehouse', 'purchase_request', 'buyer']
    date_hierarchy = 'order_date'
    inlines = [PurchaseOrderItemInline]

    fieldsets = (
        ('Informacoes Basicas', {
            'fields': ('reference_number', 'status', 'supplier', 'buyer')
        }),
        ('Detalhes', {
            'fields': ('warehouse', 'purchase_request', 'order_date', 'expected_delivery_date')
        }),
        ('Condicoes', {
            'fields': ('payment_terms', 'shipping_address', 'notes'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def total_value_display(self, obj):
        return f"R$ {obj.total_value:,.2f}"
    total_value_display.short_description = "Valor Total"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class ReceivingItemInline(admin.TabularInline):
    model = ReceivingItem
    extra = 1
    fields = (
        'purchase_order_item', 'quantity_received', 'quantity_accepted',
        'quantity_rejected', 'batch_number', 'expiry_date', 'notes'
    )


@admin.register(Receiving)
class ReceivingAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number', 'status', 'purchase_order', 'receiving_date',
        'invoice_number', 'received_by', 'total_value_display'
    )
    list_filter = ('status', 'receiving_date')
    search_fields = ('reference_number', 'purchase_order__reference_number', 'invoice_number')
    readonly_fields = ('reference_number', 'created_at', 'updated_at', 'created_by', 'updated_by')
    autocomplete_fields = ['purchase_order', 'received_by', 'inspected_by']
    date_hierarchy = 'receiving_date'
    inlines = [ReceivingItemInline]

    fieldsets = (
        ('Informacoes Basicas', {
            'fields': ('reference_number', 'status', 'purchase_order', 'receiving_date')
        }),
        ('Nota Fiscal', {
            'fields': ('invoice_number', 'invoice_date')
        }),
        ('Responsaveis', {
            'fields': ('received_by', 'inspected_by', 'inspection_date')
        }),
        ('Observacoes', {
            'fields': ('notes', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def total_value_display(self, obj):
        return f"R$ {obj.total_received_value:,.2f}"
    total_value_display.short_description = "Valor Total"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
