from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import CustomUser, UserRole


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'status', 'role', 'registration_date']
    list_filter = ['status', 'role', 'is_staff', 'is_superuser', 'registration_date']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['registration_date', 'approved_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('status', 'role', 'phone', 'department', 'registration_date')
        }),
        ('Aprovação', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_users', 'reject_users', 'suspend_users']
    
    def approve_users(self, request, queryset):
        """Ação para aprovar usuários em lote"""
        count = 0
        for user in queryset.filter(status='pending'):
            user.status = 'approved'
            user.approved_by = request.user
            user.approved_at = timezone.now()
            user.save()
            count += 1
        
        self.message_user(request, f'{count} usuário(s) aprovado(s) com sucesso.')
    approve_users.short_description = "Aprovar usuários selecionados"
    
    def reject_users(self, request, queryset):
        """Ação para rejeitar usuários em lote"""
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'{count} usuário(s) rejeitado(s) com sucesso.')
    reject_users.short_description = "Rejeitar usuários selecionados"
    
    def suspend_users(self, request, queryset):
        """Ação para suspender usuários em lote"""
        count = queryset.filter(status='approved').update(status='suspended')
        self.message_user(request, f'{count} usuário(s) suspenso(s) com sucesso.')
    suspend_users.short_description = "Suspender usuários selecionados"