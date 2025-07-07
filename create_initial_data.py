#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import UserRole, CustomUser
from django.contrib.auth.hashers import make_password

def create_roles():
    """Criar roles iniciais do sistema"""
    roles_data = [
        {
            'name': 'Administrador',
            'description': 'Acesso total ao sistema, pode gerenciar usuários e configurações',
            'permissions': [
                'manage_users', 'manage_materials', 'manage_inventory', 
                'manage_purchasing', 'view_reports', 'system_admin'
            ]
        },
        {
            'name': 'Operador de Estoque',
            'description': 'Gerencia entrada e saída de materiais no estoque',
            'permissions': [
                'view_materials', 'manage_inventory', 'print_labels', 'scan_codes'
            ]
        },
        {
            'name': 'Comprador',
            'description': 'Gerencia pedidos de compra e fornecedores',
            'permissions': [
                'view_materials', 'view_inventory', 'manage_purchasing', 'view_suppliers'
            ]
        },
        {
            'name': 'Visualizador',
            'description': 'Apenas visualização de relatórios e consultas',
            'permissions': [
                'view_materials', 'view_inventory', 'view_reports'
            ]
        }
    ]
    
    for role_data in roles_data:
        role, created = UserRole.objects.get_or_create(
            name=role_data['name'],
            defaults={
                'description': role_data['description'],
                'permissions': role_data['permissions']
            }
        )
        if created:
            print(f"✓ Role criada: {role.name}")
        else:
            print(f"- Role já existe: {role.name}")

def create_admin_user():
    """Criar usuário administrador inicial"""
    admin_role = UserRole.objects.get(name='Administrador')
    
    admin_user, created = CustomUser.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@latecme.com',
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'is_staff': True,
            'is_superuser': True,
            'status': 'approved',
            'role': admin_role,
            'password': make_password('admin123')  # Senha temporária
        }
    )
    
    if created:
        print(f"✓ Usuário administrador criado: {admin_user.username}")
        print(f"  Email: {admin_user.email}")
        print(f"  Senha: admin123")
    else:
        print(f"- Usuário administrador já existe: {admin_user.username}")

if __name__ == '__main__':
    print("Criando dados iniciais do sistema...")
    create_roles()
    create_admin_user()
    print("Dados iniciais criados com sucesso!")