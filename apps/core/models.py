from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid


class Sequence(models.Model):
    """Sequências para geração atômica de IDs"""
    name = models.CharField(max_length=100, unique=True, primary_key=True)
    prefix = models.CharField(max_length=20)
    current_value = models.PositiveIntegerField(default=0)
    date_scope = models.DateField(null=True, blank=True)
    padding = models.PositiveSmallIntegerField(default=5)

    class Meta:
        db_table = 'core_sequence'

    @classmethod
    def get_next(cls, name, prefix, padding=5, date_scope=None, extra_key=''):
        """
        Gera próximo número de forma atômica.

        Args:
            name: Identificador da sequência (ex: 'purchase_request')
            prefix: Prefixo do código (ex: 'SC', 'OP')
            padding: Zeros à esquerda (ex: 5 -> 00001)
            date_scope: Data para sequências diárias (None = global)
            extra_key: Chave extra para escopo adicional (ex: warehouse_code)

        Returns:
            str: Código formatado (ex: 'SC00001', 'OP-20260126-001')
        """
        # Montar chave única da sequência
        if date_scope:
            seq_name = f"{name}_{date_scope.strftime('%Y%m%d')}"
            if extra_key:
                seq_name = f"{seq_name}_{extra_key}"
        else:
            seq_name = name

        with transaction.atomic():
            seq, created = cls.objects.select_for_update().get_or_create(
                name=seq_name,
                defaults={
                    'prefix': prefix,
                    'current_value': 0,
                    'date_scope': date_scope,
                    'padding': padding
                }
            )
            seq.current_value += 1
            seq.save()

            # Formatar resultado
            if date_scope:
                return f"{prefix}-{date_scope.strftime('%Y%m%d')}-{seq.current_value:0{padding}d}"
            else:
                return f"{prefix}{seq.current_value:0{padding}d}"


class TimeStampedModel(models.Model):
    """Modelo abstrato com campos de timestamp"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    """Modelo base com UUID e campos de auditoria"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_updated',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True