from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import JsonResponse
from decimal import Decimal
from .models import Material, Supplier, MaterialSupplier, MaterialCategory


User = get_user_model()


class MaterialViewsTestCase(TestCase):
    """Testes para as views do módulo materials"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar usuário aprovado
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()
        
        # Criar categoria
        self.category = MaterialCategory.objects.create(
            name='Ligas de Alumínio',
            color='#3498db',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Criar materiais
        self.material1 = Material.objects.create(
            code='AL7075',
            name='Alumínio 7075-T6',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.810'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.material2 = Material.objects.create(
            code='TI6AL4V',
            name='Titânio Grade 5',
            material_type='titanium',
            category=self.category,
            density=Decimal('4.430'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Criar fornecedor
        self.supplier = Supplier.objects.create(
            code='FOR001',
            name='Alcoa Brasil',
            cnpj='12.345.678/0001-90',
            contact_email='contato@alcoa.com',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Login do usuário
        self.client.login(username='testuser', password='testpass123')
    
    def test_dashboard_materials_view(self):
        """Testa o dashboard de materiais"""
        response = self.client.get(reverse('materials:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Materiais')
        self.assertContains(response, 'Fornecedores')
        self.assertContains(response, 'Categorias')
        self.assertIn('total_materials', response.context)
        self.assertIn('total_suppliers', response.context)
        self.assertIn('total_categories', response.context)
    
    def test_material_list_view(self):
        """Testa a lista de materiais"""
        response = self.client.get(reverse('materials:list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AL7075')
        self.assertContains(response, 'TI6AL4V')
        self.assertContains(response, 'Alumínio 7075-T6')
        self.assertContains(response, 'Titânio Grade 5')
        self.assertIn('page_obj', response.context)
    
    def test_material_list_view_with_search(self):
        """Testa a lista de materiais com busca"""
        response = self.client.get(reverse('materials:list'), {'search': 'AL7075'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AL7075')
        self.assertNotContains(response, 'TI6AL4V')
    
    def test_material_list_view_with_filters(self):
        """Testa a lista de materiais com filtros"""
        response = self.client.get(reverse('materials:list'), {
            'type': 'aluminum',
            'category': str(self.category.id)
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AL7075')
        self.assertNotContains(response, 'TI6AL4V')
    
    def test_material_detail_view(self):
        """Testa a visualização de detalhes do material"""
        response = self.client.get(reverse('materials:detail', kwargs={'material_id': self.material1.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AL7075')
        self.assertContains(response, 'Alumínio 7075-T6')
        self.assertContains(response, '2.810')
        self.assertIn('material', response.context)
    
    def test_material_detail_view_not_found(self):
        """Testa a visualização de material não encontrado"""
        response = self.client.get(reverse('materials:detail', kwargs={'material_id': '12345678-1234-5678-9012-123456789012'}))
        
        self.assertEqual(response.status_code, 404)
    
    def test_material_create_view_get(self):
        """Testa a exibição do formulário de criação de material"""
        response = self.client.get(reverse('materials:create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Novo Material')
        self.assertIn('form', response.context)
    
    def test_material_create_view_post_valid(self):
        """Testa a criação de material com dados válidos"""
        data = {
            'code': 'SS316L',
            'name': 'Aço Inoxidável 316L',
            'material_type': 'steel',
            'category': self.category.id,
            'density': '8.000',
            'composition': '{"Fe": 68, "Cr": 18, "Ni": 10, "Mo": 2}',
            'specifications': '{}',
            'requires_certificate': True,
            'storage_requirements': 'Ambiente seco',
            'safety_notes': 'Usar EPI adequado'
        }
        
        response = self.client.post(reverse('materials:create'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        self.assertTrue(Material.objects.filter(code='SS316L').exists())
    
    def test_material_create_view_post_invalid(self):
        """Testa a criação de material com dados inválidos"""
        data = {
            'code': '',  # Código vazio
            'name': 'Material Teste',
            'material_type': 'aluminum',
            'density': '2.700'
        }
        
        response = self.client.post(reverse('materials:create'), data)
        
        self.assertEqual(response.status_code, 200)  # Permanece na página com erros
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_material_edit_view_get(self):
        """Testa a exibição do formulário de edição de material"""
        response = self.client.get(reverse('materials:edit', kwargs={'material_id': self.material1.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Material')
        self.assertContains(response, 'AL7075')
        self.assertIn('form', response.context)
    
    def test_material_edit_view_post_valid(self):
        """Testa a edição de material com dados válidos"""
        data = {
            'code': 'AL7075',
            'name': 'Alumínio 7075-T6 Modificado',
            'material_type': 'aluminum',
            'category': self.category.id,
            'density': '2.810',
            'composition': '{"Al": 90, "Zn": 5.6, "Mg": 2.5, "Cu": 1.6}',
            'specifications': '{}',
            'requires_certificate': True,
            'storage_requirements': 'Ambiente seco',
            'safety_notes': 'Usar EPI adequado'
        }
        
        response = self.client.post(reverse('materials:edit', kwargs={'material_id': self.material1.id}), data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        
        # Verificar se material foi atualizado
        self.material1.refresh_from_db()
        self.assertEqual(self.material1.name, 'Alumínio 7075-T6 Modificado')
    
    def test_material_search_api_view(self):
        """Testa a API de busca de materiais"""
        response = self.client.get(reverse('materials:search_api'), {'q': 'AL70'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['code'], 'AL7075')
    
    def test_material_search_api_view_short_query(self):
        """Testa a API de busca com query muito curta"""
        response = self.client.get(reverse('materials:search_api'), {'q': 'A'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 0)
    
    def test_supplier_list_view(self):
        """Testa a lista de fornecedores"""
        response = self.client.get(reverse('materials:supplier_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FOR001')
        self.assertContains(response, 'Alcoa Brasil')
        self.assertContains(response, '12.345.678/0001-90')
        self.assertIn('page_obj', response.context)
    
    def test_supplier_list_view_with_search(self):
        """Testa a lista de fornecedores com busca"""
        response = self.client.get(reverse('materials:supplier_list'), {'search': 'Alcoa'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alcoa Brasil')
    
    def test_supplier_detail_view(self):
        """Testa a visualização de detalhes do fornecedor"""
        response = self.client.get(reverse('materials:supplier_detail', kwargs={'supplier_id': self.supplier.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FOR001')
        self.assertContains(response, 'Alcoa Brasil')
        self.assertContains(response, '12.345.678/0001-90')
        self.assertIn('supplier', response.context)
    
    def test_supplier_create_view_get(self):
        """Testa a exibição do formulário de criação de fornecedor"""
        response = self.client.get(reverse('materials:supplier_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Novo Fornecedor')
        self.assertIn('form', response.context)
    
    def test_supplier_create_view_post_valid(self):
        """Testa a criação de fornecedor com dados válidos"""
        data = {
            'code': 'FOR002',
            'name': 'Titanium Industries',
            'cnpj': '98.765.432/0001-10',
            'contact_email': 'contato@titanium.com',
            'contact_phone': '(11) 99999-9999',
            'address': 'Rua das Indústrias, 456',
            'notes': 'Fornecedor especializado em titânio'
        }
        
        response = self.client.post(reverse('materials:supplier_create'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        self.assertTrue(Supplier.objects.filter(code='FOR002').exists())
    
    def test_supplier_edit_view_get(self):
        """Testa a exibição do formulário de edição de fornecedor"""
        response = self.client.get(reverse('materials:supplier_edit', kwargs={'supplier_id': self.supplier.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Fornecedor')
        self.assertContains(response, 'FOR001')
        self.assertIn('form', response.context)
    
    def test_supplier_edit_view_post_valid(self):
        """Testa a edição de fornecedor com dados válidos"""
        data = {
            'code': 'FOR001',
            'name': 'Alcoa Brasil Ltda',
            'cnpj': '12.345.678/0001-90',
            'contact_email': 'contato@alcoa.com.br',
            'contact_phone': '(11) 99999-9999',
            'address': 'Rua das Indústrias, 123',
            'notes': 'Fornecedor principal de alumínio'
        }
        
        response = self.client.post(reverse('materials:supplier_edit', kwargs={'supplier_id': self.supplier.id}), data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        
        # Verificar se fornecedor foi atualizado
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.name, 'Alcoa Brasil Ltda')
        self.assertEqual(self.supplier.contact_email, 'contato@alcoa.com.br')


class MaterialViewsPermissionTestCase(TestCase):
    """Testes de permissão para as views do módulo materials"""
    
    def setUp(self):
        self.client = Client()
        
        # Criar usuário não aprovado
        self.pending_user = User.objects.create_user(
            username='pending',
            email='pending@example.com',
            password='testpass123'
        )
        self.pending_user.status = 'pending'
        self.pending_user.save()
        
        # Criar categoria e material
        self.category = MaterialCategory.objects.create(
            name='Ligas de Alumínio',
            color='#3498db',
            created_by=self.pending_user,
            updated_by=self.pending_user
        )
        
        self.material = Material.objects.create(
            code='AL7075',
            name='Alumínio 7075-T6',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.810'),
            created_by=self.pending_user,
            updated_by=self.pending_user
        )
    
    def test_material_views_require_login(self):
        """Testa se as views requerem login"""
        urls = [
            reverse('materials:dashboard'),
            reverse('materials:list'),
            reverse('materials:detail', kwargs={'material_id': self.material.id}),
            reverse('materials:create'),
            reverse('materials:edit', kwargs={'material_id': self.material.id}),
            reverse('materials:supplier_list'),
            reverse('materials:supplier_create'),
            reverse('materials:search_api'),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirecionamento para login
    
    def test_material_views_with_pending_user(self):
        """Testa acesso com usuário pendente"""
        self.client.login(username='pending', password='testpass123')
        
        # Usuário pendente deve ser redirecionado pelo middleware
        response = self.client.get(reverse('materials:dashboard'))
        self.assertEqual(response.status_code, 302)
    
    def test_material_api_requires_login(self):
        """Testa se a API requer login"""
        response = self.client.get(reverse('materials:search_api'), {'q': 'AL70'})
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login