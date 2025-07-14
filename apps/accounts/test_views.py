from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UserRole


User = get_user_model()


class AccountViewsTestCase(TestCase):
    """Testes para as views do módulo accounts"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar usuário aprovado
        self.approved_user = User.objects.create_user(
            username='approved',
            email='approved@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.approved_user.status = 'approved'
        self.approved_user.save()
        
        # Criar usuário pendente
        self.pending_user = User.objects.create_user(
            username='pending',
            email='pending@example.com',
            password='testpass123'
        )
        self.pending_user.status = 'pending'
        self.pending_user.save()
        
        # Criar role
        self.role = UserRole.objects.create(
            name='Operador',
            description='Operador de estoque',
            permissions=['view_materials', 'change_stock'],
            created_by=self.approved_user,
            updated_by=self.approved_user
        )
    
    def test_login_view_get(self):
        """Testa a exibição da página de login"""
        response = self.client.get(reverse('accounts:login'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Usuário')
        self.assertContains(response, 'Senha')
    
    def test_login_view_post_valid_approved_user(self):
        """Testa login com usuário aprovado"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'approved',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após login
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_view_post_valid_pending_user(self):
        """Testa login com usuário pendente"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'pending',
            'password': 'testpass123'
        })
        
        # Login bem-sucedido, mas middleware redirecionará
        self.assertEqual(response.status_code, 302)
    
    def test_login_view_post_invalid(self):
        """Testa login com credenciais inválidas"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'invalid',
            'password': 'wrongpass'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'erro')
    
    def test_logout_view(self):
        """Testa logout"""
        self.client.login(username='approved', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após logout
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_register_view_get(self):
        """Testa a exibição da página de registro"""
        response = self.client.get(reverse('accounts:register'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registrar')
        self.assertContains(response, 'Usuário')
        self.assertContains(response, 'Email')
    
    def test_register_view_post_valid(self):
        """Testa registro com dados válidos"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '(11) 99999-9999',
            'department': 'TI'
        }
        
        response = self.client.post(reverse('accounts:register'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        
        # Verificar se usuário foi criado
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.status, 'pending')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
    
    def test_register_view_post_invalid(self):
        """Testa registro com dados inválidos"""
        data = {
            'username': 'newuser',
            'email': 'invalid-email',  # Email inválido
            'password1': 'testpass123',
            'password2': 'differentpass',  # Senhas diferentes
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(reverse('accounts:register'), data)
        
        self.assertEqual(response.status_code, 200)  # Permanece na página com erros
        self.assertContains(response, 'erro')
    
    def test_profile_view_authenticated(self):
        """Testa visualização de perfil com usuário autenticado"""
        self.client.login(username='approved', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'approved@example.com')
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'Aprovado')
    
    def test_profile_view_unauthenticated(self):
        """Testa visualização de perfil sem autenticação"""
        response = self.client.get(reverse('accounts:profile'))
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login
    
    def test_edit_profile_view_get(self):
        """Testa exibição do formulário de edição de perfil"""
        self.client.login(username='approved', password='testpass123')
        response = self.client.get(reverse('accounts:edit_profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Perfil')
        self.assertContains(response, 'Test')
        self.assertContains(response, 'User')
    
    def test_edit_profile_view_post_valid(self):
        """Testa edição de perfil com dados válidos"""
        self.client.login(username='approved', password='testpass123')
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '(11) 88888-8888',
            'department': 'Produção'
        }
        
        response = self.client.post(reverse('accounts:edit_profile'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        
        # Verificar se dados foram atualizados
        self.approved_user.refresh_from_db()
        self.assertEqual(self.approved_user.first_name, 'Updated')
        self.assertEqual(self.approved_user.last_name, 'Name')
        self.assertEqual(self.approved_user.phone, '(11) 88888-8888')
        self.assertEqual(self.approved_user.department, 'Produção')
    
    def test_edit_profile_view_post_invalid(self):
        """Testa edição de perfil com dados inválidos"""
        self.client.login(username='approved', password='testpass123')
        
        data = {
            'first_name': '',  # Nome vazio
            'last_name': '',   # Sobrenome vazio
            'phone': '(11) 88888-8888',
            'department': 'Produção'
        }
        
        response = self.client.post(reverse('accounts:edit_profile'), data)
        
        self.assertEqual(response.status_code, 200)  # Permanece na página com erros
        self.assertContains(response, 'erro')
    
    def test_change_password_view_get(self):
        """Testa exibição do formulário de mudança de senha"""
        self.client.login(username='approved', password='testpass123')
        response = self.client.get(reverse('accounts:change_password'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alterar Senha')
        self.assertContains(response, 'Senha atual')
        self.assertContains(response, 'Nova senha')
    
    def test_change_password_view_post_valid(self):
        """Testa mudança de senha com dados válidos"""
        self.client.login(username='approved', password='testpass123')
        
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        }
        
        response = self.client.post(reverse('accounts:change_password'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        
        # Verificar se nova senha funciona
        self.client.logout()
        login_success = self.client.login(username='approved', password='newpass123')
        self.assertTrue(login_success)
    
    def test_change_password_view_post_invalid(self):
        """Testa mudança de senha com dados inválidos"""
        self.client.login(username='approved', password='testpass123')
        
        data = {
            'old_password': 'wrongpass',  # Senha atual incorreta
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        }
        
        response = self.client.post(reverse('accounts:change_password'), data)
        
        self.assertEqual(response.status_code, 200)  # Permanece na página com erros
        self.assertContains(response, 'erro')
    
    def test_register_success_view(self):
        """Testa página de sucesso após registro"""
        response = self.client.get(reverse('accounts:register_success'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'sucesso')
        self.assertContains(response, 'aprovação')


class AccountViewsRedirectTestCase(TestCase):
    """Testes de redirecionamento para views do módulo accounts"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar usuário rejeitado
        self.rejected_user = User.objects.create_user(
            username='rejected',
            email='rejected@example.com',
            password='testpass123'
        )
        self.rejected_user.status = 'rejected'
        self.rejected_user.save()
        
        # Criar usuário suspenso
        self.suspended_user = User.objects.create_user(
            username='suspended',
            email='suspended@example.com',
            password='testpass123'
        )
        self.suspended_user.status = 'suspended'
        self.suspended_user.save()
    
    def test_rejected_user_redirect(self):
        """Testa redirecionamento de usuário rejeitado"""
        self.client.login(username='rejected', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        
        # Middleware deve redirecionar usuário rejeitado
        self.assertEqual(response.status_code, 302)
    
    def test_suspended_user_redirect(self):
        """Testa redirecionamento de usuário suspenso"""
        self.client.login(username='suspended', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        
        # Middleware deve redirecionar usuário suspenso
        self.assertEqual(response.status_code, 302)
    
    def test_unauthenticated_user_redirect(self):
        """Testa redirecionamento de usuário não autenticado"""
        protected_urls = [
            reverse('accounts:profile'),
            reverse('accounts:edit_profile'),
            reverse('accounts:change_password'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirecionamento para login