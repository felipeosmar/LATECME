from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Min
from .models import Material, Supplier, MaterialSupplier, MaterialCategory, ChemicalElement, MaterialComposition


@admin.register(ChemicalElement)
class ChemicalElementAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'atomic_number', 'atomic_weight']
    search_fields = ['symbol', 'name']
    ordering = ['atomic_number']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'colored_badge', 'material_count']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def colored_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.name
        )
    colored_badge.short_description = 'Cor'
    
    def material_count(self, obj):
        count = obj.material_set.count()
        return format_html('<strong>{}</strong>', count)
    material_count.short_description = 'Nº Materiais'


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'contact_email', 'contact_phone', 
        'material_count', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'cnpj', 'contact_email']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('code', 'name', 'cnpj')
        }),
        ('Contato', {
            'fields': ('contact_email', 'contact_phone', 'address')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Auditoria', {
            'classes': ('collapse',),
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by')
        }),
    )
    
    def material_count(self, obj):
        count = obj.materials.count()
        return format_html('<strong>{}</strong>', count)
    material_count.short_description = 'Materiais'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class MaterialSupplierInline(admin.TabularInline):
    model = MaterialSupplier
    extra = 1
    readonly_fields = ['last_price_update']
    fields = [
        'supplier', 'supplier_code', 'price_per_kg', 
        'minimum_order', 'lead_time_days', 'available', 'notes'
    ]


class MaterialCompositionInline(admin.TabularInline):
    model = MaterialComposition
    extra = 1
    fields = ['element', 'percentage', 'is_max']
    autocomplete_fields = ['element']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'material_type', 'category', 'density', 
        'supplier_count', 'best_price', 'requires_certificate', 'is_active'
    ]
    list_filter = [
        'material_type', 'category', 'requires_certificate', 
        'is_active', 'created_at'
    ]
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [MaterialCompositionInline, MaterialSupplierInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('code', 'name', 'material_type', 'category')
        }),
        ('Propriedades Físicas', {
            'fields': ('density', 'melting_point')
        }),
        ('Especificações', {
            'fields': ('specifications', 'requires_certificate')
        }),
        ('Armazenamento e Segurança', {
            'fields': ('storage_requirements', 'safety_notes')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Auditoria', {
            'classes': ('collapse',),
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by')
        }),
    )
    
    def supplier_count(self, obj):
        count = obj.suppliers.count()
        color = 'green' if count > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            count
        )
    supplier_count.short_description = 'Fornecedores'
    
    def best_price(self, obj):
        price = obj.get_best_price()
        if price:
            return format_html(
                'R$ <strong>{}</strong>/kg',
                f'{price:.2f}'
            )
        return '-'
    best_price.short_description = 'Melhor Preço'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MaterialSupplier)
class MaterialSupplierAdmin(admin.ModelAdmin):
    list_display = [
        'material_code', 'supplier_name', 'supplier_code', 
        'price_per_kg', 'minimum_order', 'lead_time_days', 
        'available', 'last_price_update'
    ]
    list_filter = [
        'available', 'material__material_type', 
        'last_price_update', 'supplier__name'
    ]
    search_fields = [
        'material__code', 'material__name', 
        'supplier__name', 'supplier_code'
    ]
    readonly_fields = ['last_price_update', 'created_at', 'updated_at']
    
    def material_code(self, obj):
        return obj.material.code
    material_code.short_description = 'Código Material'
    material_code.admin_order_field = 'material__code'
    
    def supplier_name(self, obj):
        return obj.supplier.name
    supplier_name.short_description = 'Fornecedor'
    supplier_name.admin_order_field = 'supplier__name'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Customização do admin site
admin.site.site_header = "LATECME - Sistema de Manufatura"
admin.site.site_title = "LATECME Admin"
admin.site.index_title = "Painel de Controle"