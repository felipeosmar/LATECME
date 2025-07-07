from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid


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