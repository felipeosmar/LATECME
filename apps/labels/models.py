from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.inventory.models import Bin


class LabelTemplate(BaseModel):
    """Template reutilizável para etiquetas EPL"""

    DPI_CHOICES = [
        (203, '203 DPI'),
        (300, '300 DPI'),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name="Nome do Template"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrição"
    )
    width_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(10), MaxValueValidator(500)],
        verbose_name="Largura (mm)",
        help_text="Largura da etiqueta em milímetros"
    )
    height_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(10), MaxValueValidator(500)],
        verbose_name="Altura (mm)",
        help_text="Altura da etiqueta em milímetros"
    )
    printer_dpi = models.IntegerField(
        choices=DPI_CHOICES,
        default=203,
        verbose_name="Resolução da Impressora"
    )
    template_json = models.JSONField(
        default=dict,
        verbose_name="Configuração do Template",
        help_text="JSON com elementos do template"
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Template Padrão"
    )

    class Meta:
        verbose_name = "Template de Etiqueta"
        verbose_name_plural = "Templates de Etiquetas"
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.width_mm}x{self.height_mm}mm)"

    @property
    def width_dots(self):
        """Converte largura de mm para dots"""
        return self.mm_to_dots(float(self.width_mm))

    @property
    def height_dots(self):
        """Converte altura de mm para dots"""
        return self.mm_to_dots(float(self.height_mm))

    def mm_to_dots(self, mm):
        """Converte milímetros para dots baseado no DPI"""
        return int((mm / 25.4) * self.printer_dpi)

    def save(self, *args, **kwargs):
        # Garantir apenas um template padrão
        if self.is_default:
            LabelTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class PrinterConfiguration(BaseModel):
    """Configuração de impressoras de rede"""

    name = models.CharField(
        max_length=100,
        verbose_name="Nome da Impressora"
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="Endereço IP",
        help_text="IP da impressora na rede"
    )
    port = models.IntegerField(
        default=9100,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        verbose_name="Porta TCP",
        help_text="Porta TCP padrão: 9100"
    )
    timeout_seconds = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        verbose_name="Timeout (segundos)",
        help_text="Timeout para conexão"
    )
    default_warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_printers',
        verbose_name="Armazém Padrão"
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Impressora Padrão"
    )
    last_test_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Última Verificação"
    )
    last_test_success = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Última Verificação OK"
    )

    class Meta:
        verbose_name = "Configuração de Impressora"
        verbose_name_plural = "Configurações de Impressoras"
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port})"

    @property
    def connection_info(self):
        """Retorna string com informações de conexão"""
        return f"{self.ip_address}:{self.port}"

    def save(self, *args, **kwargs):
        # Garantir apenas uma impressora padrão
        if self.is_default:
            PrinterConfiguration.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class PrintJob(BaseModel):
    """Histórico de trabalhos de impressão"""

    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando'),
        ('SUCCESS', 'Sucesso'),
        ('FAILED', 'Falhou'),
        ('CANCELLED', 'Cancelado'),
    ]

    printer = models.ForeignKey(
        PrinterConfiguration,
        on_delete=models.PROTECT,
        related_name='print_jobs',
        verbose_name="Impressora"
    )
    template = models.ForeignKey(
        LabelTemplate,
        on_delete=models.PROTECT,
        related_name='print_jobs',
        verbose_name="Template"
    )
    bin = models.ForeignKey(
        Bin,
        on_delete=models.PROTECT,
        related_name='print_jobs',
        verbose_name="Contentor"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Status"
    )
    epl_content = models.TextField(
        blank=True,
        verbose_name="Comandos EPL",
        help_text="Comandos EPL gerados"
    )
    bin_data_snapshot = models.JSONField(
        default=dict,
        verbose_name="Snapshot dos Dados",
        help_text="Dados do bin no momento da impressão"
    )
    printed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Impresso em"
    )
    error_message = models.TextField(
        blank=True,
        verbose_name="Mensagem de Erro"
    )

    class Meta:
        verbose_name = "Trabalho de Impressão"
        verbose_name_plural = "Trabalhos de Impressão"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Print Job {self.bin.code} - {self.get_status_display()}"

    @property
    def bin_code(self):
        """Retorna código do bin"""
        return self.bin.code if self.bin else 'N/A'
