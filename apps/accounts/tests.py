from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.messages import get_messages
from .models import CustomUser, UserRole


User = get_user_model()


class CustomUserTestCase(TestCase):
    """Testes para o model CustomUser"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.admin_user.status = 'approved'
        self.admin_user.save()
    
    def test_create_custom_user(self):
        """Testa a criação de usuário customizado"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='(11) 99999-9999',
            department='TI'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.phone, '(11) 99999-9999')
        self.assertEqual(user.department, 'TI')
        self.assertEqual(user.status, 'pending')  # Status padrão
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Testa a criação de superusuário"""
        superuser = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='superpass123'
        )
        
        self.assertEqual(superuser.username, 'superuser')
        self.assertEqual(superuser.email, 'super@example.com')
        self.assertEqual(superuser.status, 'approved')  # Superuser é aprovado automaticamente
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
    
    def test_user_string_representation(self):
        """Testa a representação string do usuário"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Com nome completo
        self.assertEqual(str(user), 'Test User (testuser)')
        
        # Sem nome completo
        user.first_name = ''
        user.last_name = ''
        user.save()
        self.assertEqual(str(user), 'testuser')
    
    def test_user_get_full_name(self):
        """Testa o método get_full_name"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.assertEqual(user.get_full_name(), 'Test User')
        
        # Sem nome
        user.first_name = ''
        user.last_name = ''
        user.save()
        self.assertEqual(user.get_full_name(), 'testuser')
    
    def test_user_status_choices(self):
        """Testa as opções de status do usuário"""
        valid_statuses = ['pending', 'approved', 'rejected', 'suspended']
        
        for status in valid_statuses:
            user = User.objects.create_user(
                username=f'user_{status}',
                email=f'{status}@example.com',
                password='testpass123'
            )
            user.status = status
            user.save()
            self.assertEqual(user.status, status)
    
    def test_user_email_unique(self):
        """Testa a unicidade do email"""
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='user2',
                email='test@example.com',  # Email duplicado
                password='testpass123'
            )
    
    def test_user_approval_fields(self):
        """Testa os campos de aprovação"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Aprovar usuário
        user.status = 'approved'
        user.approved_by = self.admin_user
        user.approved_at = user.updated_at
        user.save()
        
        self.assertEqual(user.status, 'approved')
        self.assertEqual(user.approved_by, self.admin_user)
        self.assertIsNotNone(user.approved_at)


class UserRoleTestCase(TestCase):
    """Testes para o model UserRole"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.admin_user.status = 'approved'
        self.admin_user.save()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()
    
    def test_create_user_role(self):
        """Testa a criação de função de usuário"""
        role = UserRole.objects.create(
            name='Operador de Estoque',
            description='Responsável por entrada e saída de materiais',
            permissions=['view_materials', 'change_stock', 'add_movement'],
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        self.assertEqual(role.name, 'Operador de Estoque')
        self.assertEqual(role.description, 'Responsável por entrada e saída de materiais')
        self.assertEqual(role.permissions, ['view_materials', 'change_stock', 'add_movement'])
        self.assertTrue(role.is_active)
        self.assertEqual(str(role), 'Operador de Estoque')
    
    def test_user_role_unique_name(self):
        """Testa a unicidade do nome da função"""
        UserRole.objects.create(
            name='Administrador',
            description='Acesso total ao sistema',
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        with self.assertRaises(Exception):
            UserRole.objects.create(
                name='Administrador',  # Nome duplicado
                description='Outra descrição',
                created_by=self.admin_user,
                updated_by=self.admin_user
            )
    
    def test_assign_role_to_user(self):
        """Testa a atribuição de função a usuário"""
        role = UserRole.objects.create(
            name='Operador de Estoque',
            description='Responsável por entrada e saída de materiais',
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Atribuir função
        self.user.role = role
        self.user.save()
        
        self.assertEqual(self.user.role, role)
        self.assertEqual(self.user.role.name, 'Operador de Estoque')
    
    def test_user_role_permissions_json(self):
        """Testa o campo JSON de permissões"""
        permissions = [
            'view_materials',
            'add_materials',
            'change_materials',
            'view_stock',
            'change_stock'
        ]
        
        role = UserRole.objects.create(
            name='Gerente de Materiais',
            description='Gerencia materiais e estoque',
            permissions=permissions,
            created_by=self.admin_user,
            updated_by=self.admin_user
        )
        
        # Verificar se as permissões foram salvas corretamente
        self.assertEqual(role.permissions, permissions)
        self.assertIn('view_materials', role.permissions)
        self.assertIn('change_stock', role.permissions)


class UserAuthenticationTestCase(TestCase):
    """Testes para autenticação e middleware"""
    
    def setUp(self):
        self.client = Client()
        self.approved_user = User.objects.create_user(
            username='approved',
            email='approved@example.com',
            password='testpass123'
        )
        self.approved_user.status = 'approved'
        self.approved_user.save()
        
        self.pending_user = User.objects.create_user(
            username='pending',
            email='pending@example.com',
            password='testpass123'
        )
        self.pending_user.status = 'pending'
        self.pending_user.save()
        
        self.rejected_user = User.objects.create_user(
            username='rejected',
            email='rejected@example.com',
            password='testpass123'
        )
        self.rejected_user.status = 'rejected'
        self.rejected_user.save()
    
    def test_login_approved_user(self):
        """Testa login de usuário aprovado"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'approved',
            'password': 'testpass123'
        })
        
        # Usuário aprovado deve ser redirecionado
        self.assertEqual(response.status_code, 302)
    
    def test_login_pending_user(self):
        """Testa login de usuário pendente"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'pending',
            'password': 'testpass123'
        })
        
        # Login bem-sucedido, mas middleware deve bloquear
        self.assertEqual(response.status_code, 302)
    
    def test_login_rejected_user(self):
        """Testa login de usuário rejeitado"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'rejected',
            'password': 'testpass123'
        })
        
        # Login bem-sucedido, mas middleware deve bloquear
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_access_approved_user(self):
        """Testa acesso ao dashboard por usuário aprovado"""
        self.client.login(username='approved', password='testpass123')
        response = self.client.get(reverse('core:dashboard'))
        
        # Usuário aprovado deve ter acesso
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_access_pending_user(self):
        """Testa acesso ao dashboard por usuário pendente"""
        self.client.login(username='pending', password='testpass123')
        response = self.client.get(reverse('core:dashboard'))
        
        # Usuário pendente deve ser redirecionado
        self.assertEqual(response.status_code, 302)
    
    def test_user_registration(self):
        """Testa registro de novo usuário"""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '(11) 99999-9999',
            'department': 'TI'
        })
        
        # Registro bem-sucedido
        self.assertEqual(response.status_code, 302)
        
        # Verificar se usuário foi criado
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.status, 'pending')
    
    def test_user_profile_view(self):
        """Testa visualização de perfil"""
        self.client.login(username='approved', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'approved@example.com')
    
    def test_password_change(self):
        """Testa mudança de senha"""
        self.client.login(username='approved', password='testpass123')
        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': 'testpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        })
        
        # Senha alterada com sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verificar se nova senha funciona
        self.client.logout()
        login_success = self.client.login(username='approved', password='newpass123')
        self.assertTrue(login_success)
    
    def test_edit_profile(self):
        """Testa edição de perfil"""
        self.client.login(username='approved', password='testpass123')
        response = self.client.post(reverse('accounts:edit_profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '(11) 88888-8888',
            'department': 'Produção'
        })
        
        # Perfil atualizado com sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verificar se dados foram atualizados
        user = User.objects.get(username='approved')
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')
        self.assertEqual(user.phone, '(11) 88888-8888')
        self.assertEqual(user.department, 'Produção')