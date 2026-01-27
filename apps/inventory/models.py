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
        indexes = [
            models.Index(fields=['is_active']),
        ]

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
        indexes = [
            models.Index(fields=['is_active']),
        ]

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
        on_delete=models.PROTECT,
        verbose_name="Material"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
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
        indexes = [
            models.Index(fields=['movement_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['warehouse', 'movement_type', 'created_at']),
        ]

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
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['count_date']),
        ]

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
