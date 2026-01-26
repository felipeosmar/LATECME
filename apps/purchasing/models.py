from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

from apps.core.models import BaseModel
from apps.materials.models import Material, Supplier
from apps.inventory.models import Warehouse
from apps.accounts.models import CustomUser


class PurchaseRequest(BaseModel):
    """Solicitacao de compra - requisicao interna para aquisicao de materiais"""

    STATUS_CHOICES = [
        ('DRAFT', 'Rascunho'),
        ('PENDING', 'Aguardando Aprovacao'),
        ('APPROVED', 'Aprovada'),
        ('REJECTED', 'Rejeitada'),
        ('ORDERED', 'Pedido Gerado'),
        ('CANCELLED', 'Cancelada'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Baixa'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'Alta'),
        ('URGENT', 'Urgente'),
    ]

    reference_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Numero de Referencia"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name="Status"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL',
        verbose_name="Prioridade"
    )
    requester = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='purchase_requests',
        verbose_name="Solicitante"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Departamento"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='purchase_requests',
        verbose_name="Armazem Destino"
    )
    request_date = models.DateField(
        default=timezone.now,
        verbose_name="Data da Solicitacao"
    )
    required_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Necessaria"
    )
    justification = models.TextField(
        blank=True,
        verbose_name="Justificativa"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observacoes"
    )

    # Aprovacao
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_requests',
        verbose_name="Aprovado por"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data da Aprovacao"
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Motivo da Rejeicao"
    )

    class Meta:
        verbose_name = "Solicitacao de Compra"
        verbose_name_plural = "Solicitacoes de Compra"
        ordering = ['-request_date', '-created_at']

    def __str__(self):
        return f"{self.reference_number} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            last_request = PurchaseRequest.objects.order_by('-created_at').first()
            if last_request and last_request.reference_number:
                try:
                    last_num = int(last_request.reference_number.replace('SC', ''))
                    self.reference_number = f"SC{last_num + 1:05d}"
                except ValueError:
                    self.reference_number = "SC00001"
            else:
                self.reference_number = "SC00001"
        super().save(*args, **kwargs)

    @property
    def total_value(self):
        """Valor total estimado da solicitacao"""
        return sum(item.total_price for item in self.items.all())

    @property
    def can_approve(self):
        return self.status == 'PENDING'

    @property
    def can_edit(self):
        return self.status in ['DRAFT', 'PENDING']


class PurchaseRequestItem(BaseModel):
    """Item de uma solicitacao de compra"""

    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Solicitacao"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='purchase_request_items',
        verbose_name="Material"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Quantidade (kg)"
    )
    estimated_unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Preco Unitario Estimado"
    )
    preferred_supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_request_items',
        verbose_name="Fornecedor Preferencial"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observacoes"
    )

    class Meta:
        verbose_name = "Item de Solicitacao"
        verbose_name_plural = "Itens de Solicitacao"

    def __str__(self):
        return f"{self.material.code} - {self.quantity} kg"

    @property
    def total_price(self):
        if self.estimated_unit_price:
            return self.quantity * self.estimated_unit_price
        return Decimal('0')


class PurchaseOrder(BaseModel):
    """Pedido de compra para fornecedor"""

    STATUS_CHOICES = [
        ('DRAFT', 'Rascunho'),
        ('SENT', 'Enviado ao Fornecedor'),
        ('CONFIRMED', 'Confirmado'),
        ('PARTIAL', 'Parcialmente Recebido'),
        ('RECEIVED', 'Recebido'),
        ('CANCELLED', 'Cancelado'),
    ]

    reference_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Numero do Pedido"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name="Status"
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name="Fornecedor"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name="Armazem Destino"
    )
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        verbose_name="Solicitacao de Origem"
    )
    order_date = models.DateField(
        default=timezone.now,
        verbose_name="Data do Pedido"
    )
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Prevista de Entrega"
    )
    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Condicoes de Pagamento"
    )
    shipping_address = models.TextField(
        blank=True,
        verbose_name="Endereco de Entrega"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observacoes"
    )

    # Aprovacao
    buyer = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name="Comprador"
    )

    class Meta:
        verbose_name = "Pedido de Compra"
        verbose_name_plural = "Pedidos de Compra"
        ordering = ['-order_date', '-created_at']

    def __str__(self):
        return f"{self.reference_number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            last_order = PurchaseOrder.objects.order_by('-created_at').first()
            if last_order and last_order.reference_number:
                try:
                    last_num = int(last_order.reference_number.replace('PC', ''))
                    self.reference_number = f"PC{last_num + 1:05d}"
                except ValueError:
                    self.reference_number = "PC00001"
            else:
                self.reference_number = "PC00001"
        super().save(*args, **kwargs)

    @property
    def total_value(self):
        """Valor total do pedido"""
        return sum(item.total_price for item in self.items.all())

    @property
    def total_received(self):
        """Total ja recebido"""
        return sum(item.received_quantity for item in self.items.all())

    @property
    def can_receive(self):
        return self.status in ['SENT', 'CONFIRMED', 'PARTIAL']


class PurchaseOrderItem(BaseModel):
    """Item de um pedido de compra"""

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Pedido"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='purchase_order_items',
        verbose_name="Material"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Quantidade (kg)"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Preco Unitario (R$/kg)"
    )
    received_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0'),
        verbose_name="Quantidade Recebida"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observacoes"
    )

    class Meta:
        verbose_name = "Item de Pedido"
        verbose_name_plural = "Itens de Pedido"

    def __str__(self):
        return f"{self.material.code} - {self.quantity} kg @ R${self.unit_price}"

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    @property
    def pending_quantity(self):
        return self.quantity - self.received_quantity

    @property
    def is_fully_received(self):
        return self.received_quantity >= self.quantity


class Receiving(BaseModel):
    """Recebimento de materiais"""

    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('INSPECTING', 'Em Inspecao'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
        ('PARTIAL', 'Parcialmente Aprovado'),
    ]

    reference_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Numero do Recebimento"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Status"
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='receivings',
        verbose_name="Pedido de Compra"
    )
    receiving_date = models.DateField(
        default=timezone.now,
        verbose_name="Data do Recebimento"
    )
    invoice_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numero da Nota Fiscal"
    )
    invoice_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data da Nota Fiscal"
    )
    received_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='receivings',
        verbose_name="Recebido por"
    )
    inspected_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspected_receivings',
        verbose_name="Inspecionado por"
    )
    inspection_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data da Inspecao"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observacoes"
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Motivo da Rejeicao"
    )

    class Meta:
        verbose_name = "Recebimento"
        verbose_name_plural = "Recebimentos"
        ordering = ['-receiving_date', '-created_at']

    def __str__(self):
        return f"{self.reference_number} - {self.purchase_order.reference_number}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            last_receiving = Receiving.objects.order_by('-created_at').first()
            if last_receiving and last_receiving.reference_number:
                try:
                    last_num = int(last_receiving.reference_number.replace('RB', ''))
                    self.reference_number = f"RB{last_num + 1:05d}"
                except ValueError:
                    self.reference_number = "RB00001"
            else:
                self.reference_number = "RB00001"
        super().save(*args, **kwargs)

    @property
    def total_received_value(self):
        """Valor total recebido"""
        return sum(item.total_value for item in self.items.all())


class ReceivingItem(BaseModel):
    """Item de um recebimento"""

    receiving = models.ForeignKey(
        Receiving,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Recebimento"
    )
    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        related_name='receiving_items',
        verbose_name="Item do Pedido"
    )
    quantity_received = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Quantidade Recebida (kg)"
    )
    quantity_accepted = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Quantidade Aceita (kg)"
    )
    quantity_rejected = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0'),
        verbose_name="Quantidade Rejeitada (kg)"
    )
    batch_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numero do Lote"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Validade"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observacoes"
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Motivo da Rejeicao"
    )

    class Meta:
        verbose_name = "Item de Recebimento"
        verbose_name_plural = "Itens de Recebimento"

    def __str__(self):
        return f"{self.purchase_order_item.material.code} - {self.quantity_received} kg"

    @property
    def total_value(self):
        qty = self.quantity_accepted if self.quantity_accepted else self.quantity_received
        return qty * self.purchase_order_item.unit_price
