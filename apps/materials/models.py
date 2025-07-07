from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel
import re


class Supplier(BaseModel):
    """Fornecedores de materiais"""
    name = models.CharField(max_length=200, verbose_name="Nome")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    contact_email = models.EmailField(verbose_name="Email de Contato")
    contact_phone = models.CharField(max_length=20, verbose_name="Telefone")
    address = models.TextField(blank=True, verbose_name="Endereço")
    notes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        # Validar CNPJ (formato básico)
        if self.cnpj:
            cnpj_clean = re.sub(r'[^0-9]', '', self.cnpj)
            if len(cnpj_clean) != 14:
                raise ValidationError({'cnpj': 'CNPJ deve ter 14 dígitos.'})


class Material(BaseModel):
    """Ligas metálicas para manufatura aditiva"""
    MATERIAL_TYPES = [
        ('AL', 'Alumínio'),
        ('TI', 'Titânio'),
        ('SS', 'Aço Inoxidável'),
        ('IN', 'Inconel'),
        ('CO', 'Cobalto-Cromo'),
        ('CU', 'Cobre'),
        ('NI', 'Níquel'),
        ('OTHER', 'Outros'),
    ]
    
    code = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Código",
        help_text="Código interno (ex: AL7075, TI6AL4V)"
    )
    name = models.CharField(max_length=200, verbose_name="Nome")
    material_type = models.CharField(
        max_length=10, 
        choices=MATERIAL_TYPES,
        verbose_name="Tipo de Material"
    )
    composition = models.JSONField(
        default=dict,
        verbose_name="Composição Química",
        help_text="Composição química em percentual {elemento: percentual}"
    )
    density = models.DecimalField(
        max_digits=5, 
        decimal_places=3,
        validators=[MinValueValidator(0.1), MaxValueValidator(25.0)],
        verbose_name="Densidade (g/cm³)",
        help_text="Densidade em g/cm³"
    )
    melting_point = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Ponto de Fusão (°C)"
    )
    specifications = models.JSONField(
        default=dict,
        verbose_name="Especificações Técnicas",
        help_text="Propriedades mecânicas, normas, etc."
    )
    requires_certificate = models.BooleanField(
        default=True,
        verbose_name="Requer Certificado",
        help_text="Material requer certificado de conformidade"
    )
    storage_requirements = models.TextField(
        blank=True,
        verbose_name="Requisitos de Armazenamento"
    )
    safety_notes = models.TextField(
        blank=True,
        verbose_name="Notas de Segurança"
    )
    suppliers = models.ManyToManyField(
        Supplier,
        through='MaterialSupplier',
        related_name='materials',
        verbose_name="Fornecedores"
    )
    
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiais"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        # Validar formato do código
        if self.code:
            # Padrão: TIPO + números/letras (ex: AL7075, TI6AL4V)
            if not re.match(r'^[A-Z]{2,4}[A-Z0-9]+$', self.code.upper()):
                raise ValidationError({
                    'code': 'Código deve seguir o padrão: TIPO + identificador (ex: AL7075, TI6AL4V)'
                })
    
    def save(self, *args, **kwargs):
        self.code = self.code.upper() if self.code else ''
        super().save(*args, **kwargs)
    
    def get_main_suppliers(self):
        """Retorna os principais fornecedores (ordenados por preço)"""
        return self.materialsupplier_set.filter(
            supplier__is_active=True
        ).order_by('price_per_kg')[:3]
    
    def get_best_price(self):
        """Retorna o melhor preço disponível"""
        supplier = self.materialsupplier_set.filter(
            supplier__is_active=True
        ).order_by('price_per_kg').first()
        return supplier.price_per_kg if supplier else None


class MaterialSupplier(BaseModel):
    """Relação Material-Fornecedor com preços e condições"""
    material = models.ForeignKey(
        Material, 
        on_delete=models.CASCADE,
        verbose_name="Material"
    )
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.CASCADE,
        verbose_name="Fornecedor"
    )
    supplier_code = models.CharField(
        max_length=100,
        verbose_name="Código do Fornecedor",
        help_text="Código do material no catálogo do fornecedor"
    )
    price_per_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Preço por Kg (R$)"
    )
    minimum_order = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        verbose_name="Pedido Mínimo (Kg)"
    )
    lead_time_days = models.IntegerField(
        verbose_name="Prazo de Entrega (dias)"
    )
    available = models.BooleanField(
        default=True,
        verbose_name="Disponível",
        help_text="Material disponível para pedido"
    )
    last_price_update = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização de Preço"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    class Meta:
        unique_together = ['material', 'supplier']
        verbose_name = "Material-Fornecedor"
        verbose_name_plural = "Materiais-Fornecedores"
        ordering = ['material__code', 'price_per_kg']
    
    def __str__(self):
        return f"{self.material.code} - {self.supplier.name} - R$ {self.price_per_kg}/kg"
    
    def calculate_total_cost(self, quantity_kg):
        """Calcula custo total para uma quantidade"""
        if quantity_kg < self.minimum_order:
            return None  # Quantidade menor que mínimo
        return float(self.price_per_kg) * float(quantity_kg)


class MaterialCategory(BaseModel):
    """Categorias para organizar materiais"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    description = models.TextField(blank=True, verbose_name="Descrição")
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        verbose_name="Cor",
        help_text="Cor para identificação visual (hex)"
    )
    
    class Meta:
        verbose_name = "Categoria de Material"
        verbose_name_plural = "Categorias de Materiais"
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Adicionar categoria aos materiais
Material.add_to_class(
    'category',
    models.ForeignKey(
        MaterialCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria"
    )
)