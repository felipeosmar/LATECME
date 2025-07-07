from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel


class UserRole(TimeStampedModel):
    """Roles/Funções do sistema"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, help_text="Lista de permissões específicas")
    
    class Meta:
        verbose_name = "Função"
        verbose_name_plural = "Funções"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """Modelo de usuário personalizado"""
    
    STATUS_CHOICES = [
        ('pending', 'Aguardando Aprovação'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('suspended', 'Suspenso'),
    ]
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Status da aprovação do usuário"
    )
    role = models.ForeignKey(
        UserRole, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Função atribuída ao usuário"
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_users'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['username']
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"
    
    def can_access_system(self):
        """Verifica se o usuário pode acessar o sistema"""
        return self.status == 'approved' and self.role is not None and self.is_active
    
    def get_permissions(self):
        """Retorna as permissões do usuário baseadas na função"""
        if self.role:
            return self.role.permissions
        return []