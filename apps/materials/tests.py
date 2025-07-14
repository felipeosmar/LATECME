from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Material, Supplier, MaterialSupplier, MaterialCategory


User = get_user_model()


class MaterialCategoryTestCase(TestCase):
    """Testes para o model MaterialCategory"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()
    
    def test_create_material_category(self):
        """Testa a criação de uma categoria de material"""
        category = MaterialCategory.objects.create(
            name='Ligas de Alumínio',
            description='Ligas baseadas em alumínio',
            color='#3498db',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(category.name, 'Ligas de Alumínio')
        self.assertEqual(category.color, '#3498db')
        self.assertTrue(category.is_active)
        self.assertEqual(str(category), 'Ligas de Alumínio')
    
    def test_category_color_validation(self):
        """Testa a validação da cor da categoria"""
        category = MaterialCategory(
            name='Test Category',
            color='invalid-color',
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            category.full_clean()


class SupplierTestCase(TestCase):
    """Testes para o model Supplier"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()
    
    def test_create_supplier(self):
        """Testa a criação de um fornecedor"""
        supplier = Supplier.objects.create(
            code='FOR001',
            name='Alcoa Brasil',
            cnpj='12.345.678/0001-90',
            contact_email='contato@alcoa.com',
            contact_phone='(11) 99999-9999',
            address='Rua das Indústrias, 123',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(supplier.code, 'FOR001')
        self.assertEqual(supplier.name, 'Alcoa Brasil')
        self.assertEqual(supplier.cnpj, '12.345.678/0001-90')
        self.assertTrue(supplier.is_active)
        self.assertEqual(str(supplier), 'FOR001 - Alcoa Brasil')
    
    def test_supplier_cnpj_validation(self):
        """Testa a validação do CNPJ do fornecedor"""
        supplier = Supplier(
            code='FOR002',
            name='Test Supplier',
            cnpj='invalid-cnpj',
            contact_email='test@example.com',
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            supplier.full_clean()
    
    def test_supplier_unique_code(self):
        """Testa a unicidade do código do fornecedor"""
        Supplier.objects.create(
            code='FOR001',
            name='Supplier 1',
            cnpj='12.345.678/0001-90',
            contact_email='supplier1@example.com',
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(Exception):
            Supplier.objects.create(
                code='FOR001',  # Código duplicado
                name='Supplier 2',
                cnpj='98.765.432/0001-10',
                contact_email='supplier2@example.com',
                created_by=self.user,
                updated_by=self.user
            )


class MaterialTestCase(TestCase):
    """Testes para o model Material"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()
        
        self.category = MaterialCategory.objects.create(
            name='Ligas de Alumínio',
            color='#3498db',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_create_material(self):
        """Testa a criação de um material"""
        material = Material.objects.create(
            code='AL7075',
            name='Alumínio 7075-T6',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.810'),
            melting_point=477,
            composition={
                'Al': 90.0,
                'Zn': 5.6,
                'Mg': 2.5,
                'Cu': 1.6
            },
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(material.code, 'AL7075')
        self.assertEqual(material.name, 'Alumínio 7075-T6')
        self.assertEqual(material.material_type, 'aluminum')
        self.assertEqual(material.density, Decimal('2.810'))
        self.assertEqual(material.category, self.category)
        self.assertTrue(material.is_active)
        self.assertEqual(str(material), 'AL7075 - Alumínio 7075-T6')
    
    def test_material_unique_code(self):
        """Testa a unicidade do código do material"""
        Material.objects.create(
            code='AL7075',
            name='Alumínio 7075-T6',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.810'),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(Exception):
            Material.objects.create(
                code='AL7075',  # Código duplicado
                name='Outro Alumínio',
                material_type='aluminum',
                category=self.category,
                density=Decimal('2.900'),
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_material_get_best_price(self):
        """Testa o método get_best_price do material"""
        material = Material.objects.create(
            code='AL7075',
            name='Alumínio 7075-T6',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.810'),
            created_by=self.user,
            updated_by=self.user
        )
        
        # Sem fornecedores, deve retornar None
        self.assertIsNone(material.get_best_price())
        
        # Criar fornecedores
        supplier1 = Supplier.objects.create(
            code='FOR001',
            name='Supplier 1',
            cnpj='12.345.678/0001-90',
            contact_email='supplier1@example.com',
            created_by=self.user,
            updated_by=self.user
        )
        
        supplier2 = Supplier.objects.create(
            code='FOR002',
            name='Supplier 2',
            cnpj='98.765.432/0001-10',
            contact_email='supplier2@example.com',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Adicionar preços
        MaterialSupplier.objects.create(
            material=material,
            supplier=supplier1,
            supplier_code='ALU001',
            price_per_kg=Decimal('85.50'),
            minimum_order=Decimal('10.0'),
            lead_time_days=15,
            created_by=self.user,
            updated_by=self.user
        )
        
        MaterialSupplier.objects.create(
            material=material,
            supplier=supplier2,
            supplier_code='ALU002',
            price_per_kg=Decimal('79.90'),
            minimum_order=Decimal('5.0'),
            lead_time_days=20,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Deve retornar o menor preço
        self.assertEqual(material.get_best_price(), Decimal('79.90'))
    
    def test_material_composition_validation(self):
        """Testa a validação da composição química"""
        material = Material(
            code='AL7075',
            name='Alumínio 7075-T6',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.810'),
            composition="invalid-json",  # JSON inválido
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            material.full_clean()


class MaterialSupplierTestCase(TestCase):
    """Testes para o model MaterialSupplier"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()
        
        self.category = MaterialCategory.objects.create(
            name='Ligas de Alumínio',
            color='#3498db',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.material = Material.objects.create(
            code='AL7075',
            name='Alumínio 7075-T6',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.810'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.supplier = Supplier.objects.create(
            code='FOR001',
            name='Alcoa Brasil',
            cnpj='12.345.678/0001-90',
            contact_email='contato@alcoa.com',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_create_material_supplier(self):
        """Testa a criação de uma relação material-fornecedor"""
        material_supplier = MaterialSupplier.objects.create(
            material=self.material,
            supplier=self.supplier,
            supplier_code='ALU001',
            price_per_kg=Decimal('85.50'),
            minimum_order=Decimal('10.0'),
            lead_time_days=15,
            available=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(material_supplier.material, self.material)
        self.assertEqual(material_supplier.supplier, self.supplier)
        self.assertEqual(material_supplier.supplier_code, 'ALU001')
        self.assertEqual(material_supplier.price_per_kg, Decimal('85.50'))
        self.assertEqual(material_supplier.minimum_order, Decimal('10.0'))
        self.assertEqual(material_supplier.lead_time_days, 15)
        self.assertTrue(material_supplier.available)
        self.assertTrue(material_supplier.is_active)
        self.assertEqual(str(material_supplier), 'AL7075 - Alcoa Brasil - R$ 85.50/kg')
    
    def test_material_supplier_unique_together(self):
        """Testa a unicidade da relação material-fornecedor"""
        MaterialSupplier.objects.create(
            material=self.material,
            supplier=self.supplier,
            supplier_code='ALU001',
            price_per_kg=Decimal('85.50'),
            minimum_order=Decimal('10.0'),
            lead_time_days=15,
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(Exception):
            MaterialSupplier.objects.create(
                material=self.material,
                supplier=self.supplier,  # Duplicação
                supplier_code='ALU002',
                price_per_kg=Decimal('90.00'),
                minimum_order=Decimal('5.0'),
                lead_time_days=10,
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_material_supplier_pricing_info(self):
        """Testa informações de preço do material-fornecedor"""
        material_supplier = MaterialSupplier.objects.create(
            material=self.material,
            supplier=self.supplier,
            supplier_code='ALU001',
            price_per_kg=Decimal('85.50'),
            minimum_order=Decimal('10.0'),
            lead_time_days=15,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Teste do método calculate_total_cost
        self.assertEqual(material_supplier.calculate_total_cost(20), 1710.0)  # 85.50 * 20
        self.assertIsNone(material_supplier.calculate_total_cost(5))  # Menor que mínimo