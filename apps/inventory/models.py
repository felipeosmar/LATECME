from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseModel
from apps.materials.models import Material
from apps.accounts.models import CustomUser
from decimal import Decimal
import uuid


class Warehouse(BaseModel):
    """Armazéns/Depósitos"""
    name = models.CharField(max_length=100, verbose_name="Nome")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descrição")
    location = models.CharField(max_length=200, verbose_name="Localização")
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Responsável"
    )
    
    class Meta:
        verbose_name = "Armazém"
        verbose_name_plural = "Armazéns"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class MaterialStock(BaseModel):
    """Estoque de materiais por armazém"""
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        verbose_name="Material"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name="Armazém"
    )
    current_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Quantidade Atual (kg)"
    )
    reserved_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Quantidade Reservada (kg)"
    )
    minimum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Estoque Mínimo (kg)"
    )
    maximum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Estoque Máximo (kg)"
    )
    location_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Código de Localização",
        help_text="Estante, prateleira, etc."
    )
    last_movement_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data da Última Movimentação"
    )
    
    class Meta:
        unique_together = ['material', 'warehouse']
        verbose_name = "Estoque de Material"
        verbose_name_plural = "Estoques de Materiais"
        ordering = ['material__code', 'warehouse__code']
    
    def __str__(self):
        return f"{self.material.code} - {self.warehouse.code} ({self.current_quantity} kg)"
    
    @property
    def available_quantity(self):
        """Quantidade disponível (atual - reservada)"""
        return self.current_quantity - self.reserved_quantity
    
    @property
    def is_low_stock(self):
        """Verifica se está com estoque baixo"""
        return self.current_quantity <= self.minimum_stock
    
    @property
    def is_out_of_stock(self):
        """Verifica se está sem estoque"""
        return self.current_quantity <= 0
    
    def can_reserve(self, quantity):
        """Verifica se pode reservar uma quantidade"""
        return self.available_quantity >= quantity


class StockMovement(BaseModel):
    """Movimentações de estoque"""
    MOVEMENT_TYPES = [
        ('IN', 'Entrada'),
        ('OUT', 'Saída'),
        ('TRANSFER', 'Transferência'),
        ('ADJUSTMENT', 'Ajuste'),
        ('RETURN', 'Devolução'),
        ('LOSS', 'Perda'),
    ]
    
    MOVEMENT_REASONS = [
        ('PURCHASE', 'Compra'),
        ('PRODUCTION', 'Produção'),
        ('SALE', 'Venda'),
        ('INTERNAL_USE', 'Uso Interno'),
        ('TRANSFER', 'Transferência'),
        ('INVENTORY_ADJUSTMENT', 'Ajuste de Inventário'),
        ('EXPIRED', 'Vencido'),
        ('DAMAGED', 'Danificado'),
        ('LOST', 'Perdido'),
        ('RETURN', 'Devolução'),
        ('OTHER', 'Outros'),
    ]
    
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        verbose_name="Material"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name="Armazém"
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        verbose_name="Tipo de Movimentação"
    )
    reason = models.CharField(
        max_length=50,
        choices=MOVEMENT_REASONS,
        verbose_name="Motivo"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        verbose_name="Quantidade (kg)"
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Custo Unitário (R$/kg)"
    )
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Custo Total (R$)"
    )
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Número do Lote"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Vencimento"
    )
    certificate_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Número do Certificado"
    )
    reference_document = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Documento de Referência",
        help_text="Número da nota fiscal, pedido, etc."
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuário"
    )
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_movements',
        verbose_name="Armazém Destino",
        help_text="Para transferências"
    )
    
    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.material.code} - {self.quantity} kg"
    
    def save(self, *args, **kwargs):
        # Calcular custo total se não fornecido
        if self.unit_cost and not self.total_cost:
            self.total_cost = self.quantity * self.unit_cost
        
        super().save(*args, **kwargs)
        
        # Atualizar estoque após salvar
        self.update_stock()
    
    def update_stock(self):
        """Atualiza o estoque baseado na movimentação"""
        # Obter ou criar registro de estoque
        stock, created = MaterialStock.objects.get_or_create(
            material=self.material,
            warehouse=self.warehouse,
            defaults={
                'current_quantity': Decimal('0.000'),
                'reserved_quantity': Decimal('0.000'),
                'minimum_stock': Decimal('0.000'),
            }
        )
        
        # Aplicar movimentação
        if self.movement_type == 'IN':
            stock.current_quantity += self.quantity
        elif self.movement_type == 'OUT':
            stock.current_quantity -= self.quantity
        elif self.movement_type == 'TRANSFER':
            # Saída do armazém origem
            stock.current_quantity -= self.quantity
            
            # Entrada no armazém destino
            if self.destination_warehouse:
                dest_stock, _ = MaterialStock.objects.get_or_create(
                    material=self.material,
                    warehouse=self.destination_warehouse,
                    defaults={
                        'current_quantity': Decimal('0.000'),
                        'reserved_quantity': Decimal('0.000'),
                        'minimum_stock': Decimal('0.000'),
                    }
                )
                dest_stock.current_quantity += self.quantity
                dest_stock.last_movement_date = timezone.now()
                dest_stock.save()
        elif self.movement_type == 'ADJUSTMENT':
            # Para ajustes, a quantidade pode ser positiva ou negativa
            stock.current_quantity = self.quantity
        
        # Garantir que não fique negativo
        if stock.current_quantity < 0:
            stock.current_quantity = Decimal('0.000')
        
        stock.last_movement_date = timezone.now()
        stock.save()


class StockReservation(BaseModel):
    """Reservas de estoque"""
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        verbose_name="Material"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name="Armazém"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
        verbose_name="Quantidade Reservada (kg)"
    )
    reserved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Reservado por"
    )
    reservation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Reserva"
    )
    expiry_date = models.DateTimeField(
        verbose_name="Data de Expiração"
    )
    purpose = models.CharField(
        max_length=200,
        verbose_name="Finalidade",
        help_text="Para que será usado o material"
    )
    reference_document = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Documento de Referência"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    class Meta:
        verbose_name = "Reserva de Estoque"
        verbose_name_plural = "Reservas de Estoque"
        ordering = ['-reservation_date']
    
    def __str__(self):
        return f"{self.material.code} - {self.quantity} kg reservado por {self.reserved_by.get_full_name()}"
    
    @property
    def is_expired(self):
        """Verifica se a reserva está expirada"""
        return timezone.now() > self.expiry_date
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Atualizar quantidade reservada no estoque
        try:
            stock = MaterialStock.objects.get(
                material=self.material,
                warehouse=self.warehouse
            )
            
            # Recalcular total de reservas
            total_reserved = StockReservation.objects.filter(
                material=self.material,
                warehouse=self.warehouse,
                expiry_date__gt=timezone.now()
            ).aggregate(
                total=models.Sum('quantity')
            )['total'] or Decimal('0.000')
            
            stock.reserved_quantity = total_reserved
            stock.save()
            
        except MaterialStock.DoesNotExist:
            pass
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        
        # Atualizar quantidade reservada no estoque
        try:
            stock = MaterialStock.objects.get(
                material=self.material,
                warehouse=self.warehouse
            )
            
            # Recalcular total de reservas
            total_reserved = StockReservation.objects.filter(
                material=self.material,
                warehouse=self.warehouse,
                expiry_date__gt=timezone.now()
            ).aggregate(
                total=models.Sum('quantity')
            )['total'] or Decimal('0.000')
            
            stock.reserved_quantity = total_reserved
            stock.save()
            
        except MaterialStock.DoesNotExist:
            pass


class InventoryCount(BaseModel):
    """Contagens de inventário"""
    STATUS_CHOICES = [
        ('PLANNED', 'Planejado'),
        ('IN_PROGRESS', 'Em Andamento'),
        ('COMPLETED', 'Concluído'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número de Referência"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name="Armazém"
    )
    count_date = models.DateField(
        verbose_name="Data da Contagem"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED',
        verbose_name="Status"
    )
    counter = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_counts',
        verbose_name="Contador"
    )
    supervisor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='supervised_counts',
        verbose_name="Supervisor"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    class Meta:
        verbose_name = "Contagem de Inventário"
        verbose_name_plural = "Contagens de Inventário"
        ordering = ['-count_date']
    
    def __str__(self):
        return f"{self.reference_number} - {self.warehouse.code} ({self.count_date})"
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            # Gerar número de referência automático
            today = timezone.now().date()
            count = InventoryCount.objects.filter(
                count_date=today,
                warehouse=self.warehouse
            ).count()
            self.reference_number = f"INV-{self.warehouse.code}-{today.strftime('%Y%m%d')}-{count + 1:03d}"
        
        super().save(*args, **kwargs)


class InventoryCountItem(BaseModel):
    """Itens da contagem de inventário"""
    inventory_count = models.ForeignKey(
        InventoryCount,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Contagem"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        verbose_name="Material"
    )
    system_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Quantidade Sistema (kg)"
    )
    counted_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Quantidade Contada (kg)"
    )
    location_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Código de Localização"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    class Meta:
        unique_together = ['inventory_count', 'material']
        verbose_name = "Item de Contagem"
        verbose_name_plural = "Itens de Contagem"
        ordering = ['material__code']
    
    def __str__(self):
        return f"{self.inventory_count.reference_number} - {self.material.code}"
    
    @property
    def variance(self):
        """Diferença entre sistema e contado"""
        if self.counted_quantity is not None:
            return self.counted_quantity - self.system_quantity
        return None
    
    @property
    def variance_percentage(self):
        """Percentual de variação"""
        if self.counted_quantity is not None and self.system_quantity > 0:
            return (self.variance / self.system_quantity) * 100
        return None


class ProductionOrder(BaseModel):
    """Ordens de Produção"""
    STATUS_CHOICES = [
        ('DRAFT', 'Rascunho'),
        ('PLANNED', 'Planejado'),
        ('IN_PROGRESS', 'Em Andamento'),
        ('COMPLETED', 'Concluído'),
        ('CANCELLED', 'Cancelado'),
    ]

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número da Ordem"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name="Material a Produzir",
        related_name='production_orders'
    )
    planned_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Quantidade Planejada (kg)"
    )
    produced_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[MinValueValidator(Decimal('0.000'))],
        verbose_name="Quantidade Produzida (kg)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name="Status"
    )
    planned_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Início Planejada"
    )
    planned_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Fim Planejada"
    )
    actual_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data/Hora Início Real"
    )
    actual_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data/Hora Fim Real"
    )
    responsible = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_orders_responsible',
        verbose_name="Responsável"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Ordem de Produção"
        verbose_name_plural = "Ordens de Produção"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.material.code}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Gerar número automático: OP-YYYYMMDD-NNN
            today = timezone.now().date()
            count = ProductionOrder.objects.filter(
                created_at__date=today
            ).count()
            self.order_number = f"OP-{today.strftime('%Y%m%d')}-{count + 1:03d}"
        super().save(*args, **kwargs)

    @property
    def completion_percentage(self):
        """Percentual de conclusão"""
        if self.planned_quantity > 0:
            return (self.produced_quantity / self.planned_quantity) * 100
        return Decimal('0.00')

    @property
    def is_overdue(self):
        """Verifica se está atrasada"""
        if self.planned_end_date and self.status not in ['COMPLETED', 'CANCELLED']:
            return timezone.now().date() > self.planned_end_date
        return False

    def can_start(self):
        """Verifica se pode iniciar"""
        return self.status in ['DRAFT', 'PLANNED']

    def start(self, user=None):
        """Inicia a ordem de produção"""
        if self.can_start():
            self.status = 'IN_PROGRESS'
            self.actual_start_date = timezone.now()
            if user:
                self.updated_by = user
            self.save()
            return True
        return False

    def complete(self, user=None):
        """Conclui a ordem de produção"""
        if self.status == 'IN_PROGRESS':
            self.status = 'COMPLETED'
            self.actual_end_date = timezone.now()
            if user:
                self.updated_by = user
            self.save()
            return True
        return False


class Bin(BaseModel):
    """Contentores para armazenamento de material"""
    STATUS_CHOICES = [
        ('EMPTY', 'Vazio'),
        ('LOADED', 'Carregado'),
        ('IN_USE', 'Em Uso'),
        ('MAINTENANCE', 'Em Manutenção'),
    ]

    code = models.CharField(
        max_length=50,
        verbose_name="Código do Contentor"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='bins',
        verbose_name="Armazém"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='EMPTY',
        verbose_name="Status"
    )
    capacity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Capacidade (kg)",
        help_text="Capacidade máxima informativa"
    )
    # Conteúdo atual (desnormalizado para acesso rápido)
    current_material = models.ForeignKey(
        Material,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bins',
        verbose_name="Material Atual"
    )
    current_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[MinValueValidator(Decimal('0.000'))],
        verbose_name="Quantidade Atual (kg)"
    )
    current_supplier_batch = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Lote do Fornecedor Atual"
    )
    current_certificate = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Certificado Atual"
    )
    location_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Código de Localização",
        help_text="Estante, prateleira, posição"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        unique_together = ['warehouse', 'code']
        verbose_name = "Contentor"
        verbose_name_plural = "Contentores"
        ordering = ['warehouse__code', 'code']

    def __str__(self):
        status_display = f" ({self.current_quantity} kg de {self.current_material.code})" if self.current_material else " (Vazio)"
        return f"{self.code}{status_display}"

    @property
    def is_empty(self):
        return self.current_quantity <= 0 or self.current_material is None

    @property
    def is_loaded(self):
        return self.current_quantity > 0 and self.current_material is not None

    def clean(self):
        super().clean()
        # Validar que se há quantidade, deve haver material
        if self.current_quantity > 0 and not self.current_material:
            raise ValidationError({
                'current_material': 'Material é obrigatório quando há quantidade no contentor.'
            })

    def load_material(self, material, quantity, supplier_batch='', certificate='', user=None):
        """Carrega material no contentor"""
        if not self.is_empty and self.current_material != material:
            raise ValidationError(
                f"Contentor já contém {self.current_material.code}. Esvazie primeiro."
            )

        self.current_material = material
        self.current_quantity += quantity
        self.current_supplier_batch = supplier_batch or self.current_supplier_batch
        self.current_certificate = certificate or self.current_certificate
        self.status = 'LOADED'

        if user:
            self.updated_by = user
        self.save()

        # Criar entrada no histórico
        BinHistory.objects.create(
            bin=self,
            movement_type='IN',
            material=material,
            quantity=quantity,
            supplier_batch=supplier_batch,
            certificate=certificate,
            performed_by=user,
            created_by=user,
            updated_by=user
        )

        return True

    def unload_material(self, quantity, batch=None, user=None, notes=''):
        """Remove material do contentor"""
        if self.is_empty:
            raise ValidationError("Contentor está vazio.")

        if quantity > self.current_quantity:
            raise ValidationError(
                f"Quantidade solicitada ({quantity} kg) excede quantidade disponível ({self.current_quantity} kg)."
            )

        material = self.current_material
        supplier_batch = self.current_supplier_batch
        certificate = self.current_certificate

        self.current_quantity -= quantity

        if self.current_quantity <= 0:
            # Esvaziar completamente o contentor
            self.current_quantity = Decimal('0.000')
            self.current_material = None
            self.current_supplier_batch = ''
            self.current_certificate = ''
            self.status = 'EMPTY'

        if user:
            self.updated_by = user
        self.save()

        # Criar entrada no histórico
        BinHistory.objects.create(
            bin=self,
            movement_type='OUT',
            material=material,
            quantity=quantity,
            supplier_batch=supplier_batch,
            certificate=certificate,
            batch=batch,
            performed_by=user,
            notes=notes,
            created_by=user,
            updated_by=user
        )

        return True

    def empty(self, user=None, notes=''):
        """Esvazia completamente o contentor"""
        if self.is_empty:
            return True

        quantity = self.current_quantity
        material = self.current_material
        supplier_batch = self.current_supplier_batch
        certificate = self.current_certificate

        self.current_quantity = Decimal('0.000')
        self.current_material = None
        self.current_supplier_batch = ''
        self.current_certificate = ''
        self.status = 'EMPTY'

        if user:
            self.updated_by = user
        self.save()

        # Criar entrada no histórico
        BinHistory.objects.create(
            bin=self,
            movement_type='EMPTY',
            material=material,
            quantity=quantity,
            supplier_batch=supplier_batch,
            certificate=certificate,
            performed_by=user,
            notes=notes,
            created_by=user,
            updated_by=user
        )

        return True


class Batch(BaseModel):
    """Batelada - coleção de material de múltiplos contentores para produção"""
    STATUS_CHOICES = [
        ('PREPARATION', 'Em Preparação'),
        ('READY', 'Pronta'),
        ('IN_PRODUCTION', 'Em Produção'),
        ('COMPLETED', 'Concluída'),
        ('CANCELLED', 'Cancelada'),
    ]

    batch_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número da Batelada"
    )
    production_order = models.ForeignKey(
        ProductionOrder,
        on_delete=models.PROTECT,
        related_name='batches',
        verbose_name="Ordem de Produção"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name="Material",
        help_text="Material que compõe a batelada"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PREPARATION',
        verbose_name="Status"
    )
    target_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Quantidade Alvo (kg)"
    )
    actual_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[MinValueValidator(Decimal('0.000'))],
        verbose_name="Quantidade Real (kg)"
    )
    prepared_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='batches_prepared',
        verbose_name="Preparado por"
    )
    preparation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Preparação"
    )
    production_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Início da Produção"
    )
    completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Conclusão"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Batelada"
        verbose_name_plural = "Bateladas"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.batch_number} - {self.material.code} ({self.actual_quantity} kg)"

    def save(self, *args, **kwargs):
        if not self.batch_number:
            # Gerar número automático: BAT-YYYYMMDD-NNN
            today = timezone.now().date()
            count = Batch.objects.filter(
                created_at__date=today
            ).count()
            self.batch_number = f"BAT-{today.strftime('%Y%m%d')}-{count + 1:03d}"

        # Definir material da ordem de produção se não definido
        if not self.material_id and self.production_order_id:
            self.material = self.production_order.material

        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # Validar que material corresponde à ordem de produção
        if self.material_id and self.production_order_id:
            if self.material != self.production_order.material:
                raise ValidationError({
                    'material': 'Material deve ser o mesmo da Ordem de Produção.'
                })

    @property
    def quantity_variance(self):
        """Diferença entre quantidade alvo e real"""
        return self.actual_quantity - self.target_quantity

    @property
    def is_complete(self):
        """Verifica se atingiu a quantidade alvo"""
        return self.actual_quantity >= self.target_quantity

    def add_bin_material(self, bin_obj, quantity, user=None):
        """Adiciona material de um contentor à batelada"""
        if self.status not in ['PREPARATION', 'READY']:
            raise ValidationError("Batelada não está em preparação.")

        if bin_obj.is_empty:
            raise ValidationError(f"Contentor {bin_obj.code} está vazio.")

        if bin_obj.current_material != self.material:
            raise ValidationError(
                f"Material do contentor ({bin_obj.current_material.code}) "
                f"não corresponde ao material da batelada ({self.material.code})."
            )

        if quantity > bin_obj.current_quantity:
            raise ValidationError(
                f"Quantidade solicitada ({quantity} kg) excede disponível no contentor ({bin_obj.current_quantity} kg)."
            )

        # Criar item da batelada
        batch_item = BatchItem.objects.create(
            batch=self,
            bin=bin_obj,
            material=self.material,
            quantity=quantity,
            supplier_batch=bin_obj.current_supplier_batch,
            certificate=bin_obj.current_certificate,
            collected_by=user,
            created_by=user,
            updated_by=user
        )

        # Descarregar do contentor (isso cria histórico)
        bin_obj.unload_material(
            quantity=quantity,
            batch=self,
            user=user,
            notes=f"Material coletado para batelada {self.batch_number}"
        )

        # Atualizar quantidade real da batelada
        self.actual_quantity += quantity
        if user:
            self.updated_by = user
        self.save()

        return batch_item

    def mark_ready(self, user=None):
        """Marca batelada como pronta"""
        if self.status != 'PREPARATION':
            raise ValidationError("Batelada não está em preparação.")

        if self.actual_quantity <= 0:
            raise ValidationError("Batelada não possui material coletado.")

        self.status = 'READY'
        self.preparation_date = timezone.now()
        self.prepared_by = user
        if user:
            self.updated_by = user
        self.save()
        return True

    def start_production(self, user=None):
        """Inicia produção com a batelada"""
        if self.status != 'READY':
            raise ValidationError("Batelada não está pronta.")

        self.status = 'IN_PRODUCTION'
        self.production_start_date = timezone.now()
        if user:
            self.updated_by = user
        self.save()

        # Atualizar status da ordem de produção se necessário
        if self.production_order.status in ['DRAFT', 'PLANNED']:
            self.production_order.start(user)

        return True

    def complete(self, user=None):
        """Conclui a batelada"""
        if self.status != 'IN_PRODUCTION':
            raise ValidationError("Batelada não está em produção.")

        self.status = 'COMPLETED'
        self.completion_date = timezone.now()
        if user:
            self.updated_by = user
        self.save()

        # Atualizar quantidade produzida da ordem
        self.production_order.produced_quantity += self.actual_quantity
        self.production_order.save()

        return True


class BinHistory(BaseModel):
    """Histórico de movimentações do contentor"""
    MOVEMENT_TYPES = [
        ('IN', 'Entrada'),
        ('OUT', 'Saída'),
        ('EMPTY', 'Esvaziamento'),
        ('TRANSFER', 'Transferência'),
        ('ADJUSTMENT', 'Ajuste'),
    ]

    bin = models.ForeignKey(
        Bin,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name="Contentor"
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        verbose_name="Tipo de Movimentação"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name="Material"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Quantidade (kg)"
    )
    quantity_before = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Quantidade Antes (kg)"
    )
    quantity_after = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Quantidade Depois (kg)"
    )
    supplier_batch = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Lote do Fornecedor"
    )
    certificate = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Número do Certificado"
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bin_history_entries',
        verbose_name="Batelada",
        help_text="Batelada para a qual o material foi usado"
    )
    performed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bin_movements_performed',
        verbose_name="Realizado por"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Histórico do Contentor"
        verbose_name_plural = "Históricos dos Contentores"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bin.code} - {self.get_movement_type_display()} - {self.quantity} kg"

    def save(self, *args, **kwargs):
        # Calcular quantity_before e quantity_after se não definidos
        if not self.pk:
            last_history = BinHistory.objects.filter(
                bin=self.bin
            ).order_by('-created_at').first()

            if last_history:
                self.quantity_before = last_history.quantity_after
            else:
                self.quantity_before = Decimal('0.000')

            if self.movement_type == 'IN':
                self.quantity_after = self.quantity_before + self.quantity
            elif self.movement_type in ['OUT', 'EMPTY']:
                self.quantity_after = max(Decimal('0.000'), self.quantity_before - self.quantity)
            else:
                self.quantity_after = self.quantity_before

        super().save(*args, **kwargs)


class BatchItem(BaseModel):
    """Itens da batelada - material coletado de cada contentor"""
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Batelada"
    )
    bin = models.ForeignKey(
        Bin,
        on_delete=models.SET_NULL,
        null=True,
        related_name='batch_items',
        verbose_name="Contentor"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name="Material"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Quantidade (kg)"
    )
    supplier_batch = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Lote do Fornecedor"
    )
    certificate = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Certificado"
    )
    collected_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='batch_items_collected',
        verbose_name="Coletado por"
    )
    collected_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data/Hora da Coleta"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )

    class Meta:
        verbose_name = "Item da Batelada"
        verbose_name_plural = "Itens da Batelada"
        ordering = ['collected_at']

    def __str__(self):
        bin_code = self.bin.code if self.bin else "N/A"
        return f"{self.batch.batch_number} - {bin_code} - {self.quantity} kg"