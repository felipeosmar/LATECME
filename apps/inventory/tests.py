from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from .models import Warehouse, MaterialStock, StockMovement, StockReservation, InventoryCount, InventoryCountItem
from apps.materials.models import Material, MaterialCategory


User = get_user_model()


class WarehouseTestCase(TestCase):
    """Testes para o model Warehouse"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()
    
    def test_create_warehouse(self):
        """Testa a criação de um armazém"""
        warehouse = Warehouse.objects.create(
            code='WH001',
            name='Armazém Principal',
            address='Rua da Indústria, 123',
            manager_name='João Silva',
            manager_email='joao@empresa.com',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(warehouse.code, 'WH001')
        self.assertEqual(warehouse.name, 'Armazém Principal')
        self.assertEqual(warehouse.manager_name, 'João Silva')
        self.assertTrue(warehouse.is_active)
        self.assertEqual(str(warehouse), 'WH001 - Armazém Principal')
    
    def test_warehouse_unique_code(self):
        """Testa a unicidade do código do armazém"""
        Warehouse.objects.create(
            code='WH001',
            name='Armazém 1',
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(Exception):
            Warehouse.objects.create(
                code='WH001',  # Código duplicado
                name='Armazém 2',
                created_by=self.user,
                updated_by=self.user
            )


class MaterialStockTestCase(TestCase):
    """Testes para o model MaterialStock"""
    
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
        
        self.warehouse = Warehouse.objects.create(
            code='WH001',
            name='Armazém Principal',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_create_material_stock(self):
        """Testa a criação de estoque de material"""
        stock = MaterialStock.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('100.0'),
            reserved_quantity=Decimal('10.0'),
            minimum_stock=Decimal('20.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(stock.material, self.material)
        self.assertEqual(stock.warehouse, self.warehouse)
        self.assertEqual(stock.quantity, Decimal('100.0'))
        self.assertEqual(stock.reserved_quantity, Decimal('10.0'))
        self.assertEqual(stock.minimum_stock, Decimal('20.0'))
        self.assertTrue(stock.is_active)
        self.assertEqual(str(stock), 'AL7075 - WH001 (100.0 kg)')
    
    def test_available_quantity_property(self):
        """Testa a propriedade available_quantity"""
        stock = MaterialStock.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('100.0'),
            reserved_quantity=Decimal('15.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(stock.available_quantity, Decimal('85.0'))
    
    def test_is_low_stock_property(self):
        """Testa a propriedade is_low_stock"""
        stock = MaterialStock.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('15.0'),
            minimum_stock=Decimal('20.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertTrue(stock.is_low_stock)
    
    def test_is_out_of_stock_property(self):
        """Testa a propriedade is_out_of_stock"""
        stock = MaterialStock.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('0.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertTrue(stock.is_out_of_stock)
    
    def test_stock_unique_together(self):
        """Testa a unicidade de material por armazém"""
        MaterialStock.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('100.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(Exception):
            MaterialStock.objects.create(
                material=self.material,
                warehouse=self.warehouse,  # Duplicação
                quantity=Decimal('50.0'),
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_negative_quantity_validation(self):
        """Testa a validação de quantidade negativa"""
        stock = MaterialStock(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('-10.0'),  # Quantidade negativa
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            stock.full_clean()


class StockMovementTestCase(TestCase):
    """Testes para o model StockMovement"""
    
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
        
        self.warehouse = Warehouse.objects.create(
            code='WH001',
            name='Armazém Principal',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock = MaterialStock.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('100.0'),
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_create_stock_movement_in(self):
        """Testa a criação de movimentação de entrada"""
        movement = StockMovement.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            movement_type='in',
            quantity=Decimal('50.0'),
            description='Compra de material',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(movement.material, self.material)
        self.assertEqual(movement.warehouse, self.warehouse)
        self.assertEqual(movement.movement_type, 'in')
        self.assertEqual(movement.quantity, Decimal('50.0'))
        self.assertEqual(movement.description, 'Compra de material')
        self.assertTrue(movement.is_active)
        self.assertEqual(str(movement), 'AL7075 - WH001 (Entrada: 50.0 kg)')
    
    def test_create_stock_movement_out(self):
        """Testa a criação de movimentação de saída"""
        movement = StockMovement.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            movement_type='out',
            quantity=Decimal('25.0'),
            description='Uso em produção',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(movement.movement_type, 'out')
        self.assertEqual(movement.quantity, Decimal('25.0'))
        self.assertEqual(str(movement), 'AL7075 - WH001 (Saída: 25.0 kg)')
    
    def test_create_stock_movement_transfer(self):
        """Testa a criação de movimentação de transferência"""
        warehouse2 = Warehouse.objects.create(
            code='WH002',
            name='Armazém Secundário',
            created_by=self.user,
            updated_by=self.user
        )
        
        movement = StockMovement.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            movement_type='transfer',
            quantity=Decimal('30.0'),
            transfer_to_warehouse=warehouse2,
            description='Transferência entre armazéns',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(movement.movement_type, 'transfer')
        self.assertEqual(movement.transfer_to_warehouse, warehouse2)
        self.assertEqual(str(movement), 'AL7075 - WH001 (Transferência: 30.0 kg)')
    
    def test_negative_quantity_validation(self):
        """Testa a validação de quantidade negativa"""
        movement = StockMovement(
            material=self.material,
            warehouse=self.warehouse,
            movement_type='in',
            quantity=Decimal('-10.0'),  # Quantidade negativa
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            movement.full_clean()


class StockReservationTestCase(TestCase):
    """Testes para o model StockReservation"""
    
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
        
        self.warehouse = Warehouse.objects.create(
            code='WH001',
            name='Armazém Principal',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.stock = MaterialStock.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('100.0'),
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_create_stock_reservation(self):
        """Testa a criação de reserva de estoque"""
        expiry_date = timezone.now() + timedelta(days=7)
        
        reservation = StockReservation.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('20.0'),
            purpose='Ordem de produção #123',
            expiry_date=expiry_date,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(reservation.material, self.material)
        self.assertEqual(reservation.warehouse, self.warehouse)
        self.assertEqual(reservation.quantity, Decimal('20.0'))
        self.assertEqual(reservation.purpose, 'Ordem de produção #123')
        self.assertEqual(reservation.expiry_date, expiry_date)
        self.assertTrue(reservation.is_active)
        self.assertEqual(str(reservation), 'AL7075 - WH001 (20.0 kg)')
    
    def test_is_expired_property(self):
        """Testa a propriedade is_expired"""
        # Reserva expirada
        past_date = timezone.now() - timedelta(days=1)
        expired_reservation = StockReservation.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('10.0'),
            expiry_date=past_date,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertTrue(expired_reservation.is_expired)
        
        # Reserva válida
        future_date = timezone.now() + timedelta(days=7)
        valid_reservation = StockReservation.objects.create(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('15.0'),
            expiry_date=future_date,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertFalse(valid_reservation.is_expired)
    
    def test_negative_quantity_validation(self):
        """Testa a validação de quantidade negativa"""
        reservation = StockReservation(
            material=self.material,
            warehouse=self.warehouse,
            quantity=Decimal('-5.0'),  # Quantidade negativa
            expiry_date=timezone.now() + timedelta(days=7),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            reservation.full_clean()


class InventoryCountTestCase(TestCase):
    """Testes para o model InventoryCount"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()
        
        self.warehouse = Warehouse.objects.create(
            code='WH001',
            name='Armazém Principal',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_create_inventory_count(self):
        """Testa a criação de contagem de inventário"""
        count = InventoryCount.objects.create(
            warehouse=self.warehouse,
            reference_number='COUNT-001',
            count_date=timezone.now().date(),
            counter_name='Maria Silva',
            status='in_progress',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(count.warehouse, self.warehouse)
        self.assertEqual(count.reference_number, 'COUNT-001')
        self.assertEqual(count.counter_name, 'Maria Silva')
        self.assertEqual(count.status, 'in_progress')
        self.assertTrue(count.is_active)
        self.assertEqual(str(count), 'COUNT-001 - WH001')
    
    def test_inventory_count_unique_reference(self):
        """Testa a unicidade do número de referência"""
        InventoryCount.objects.create(
            warehouse=self.warehouse,
            reference_number='COUNT-001',
            count_date=timezone.now().date(),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(Exception):
            InventoryCount.objects.create(
                warehouse=self.warehouse,
                reference_number='COUNT-001',  # Referência duplicada
                count_date=timezone.now().date(),
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_inventory_count_status_choices(self):
        """Testa as opções de status da contagem"""
        valid_statuses = ['planning', 'in_progress', 'completed', 'cancelled']
        
        for status in valid_statuses:
            count = InventoryCount.objects.create(
                warehouse=self.warehouse,
                reference_number=f'COUNT-{status}',
                count_date=timezone.now().date(),
                status=status,
                created_by=self.user,
                updated_by=self.user
            )
            self.assertEqual(count.status, status)


class InventoryCountItemTestCase(TestCase):
    """Testes para o model InventoryCountItem"""
    
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
        
        self.warehouse = Warehouse.objects.create(
            code='WH001',
            name='Armazém Principal',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.inventory_count = InventoryCount.objects.create(
            warehouse=self.warehouse,
            reference_number='COUNT-001',
            count_date=timezone.now().date(),
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_create_inventory_count_item(self):
        """Testa a criação de item de contagem"""
        item = InventoryCountItem.objects.create(
            inventory_count=self.inventory_count,
            material=self.material,
            system_quantity=Decimal('100.0'),
            counted_quantity=Decimal('98.5'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(item.inventory_count, self.inventory_count)
        self.assertEqual(item.material, self.material)
        self.assertEqual(item.system_quantity, Decimal('100.0'))
        self.assertEqual(item.counted_quantity, Decimal('98.5'))
        self.assertTrue(item.is_active)
        self.assertEqual(str(item), 'COUNT-001 - AL7075')
    
    def test_variance_property(self):
        """Testa a propriedade variance"""
        item = InventoryCountItem.objects.create(
            inventory_count=self.inventory_count,
            material=self.material,
            system_quantity=Decimal('100.0'),
            counted_quantity=Decimal('98.5'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(item.variance, Decimal('-1.5'))
    
    def test_variance_percentage_property(self):
        """Testa a propriedade variance_percentage"""
        item = InventoryCountItem.objects.create(
            inventory_count=self.inventory_count,
            material=self.material,
            system_quantity=Decimal('100.0'),
            counted_quantity=Decimal('98.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(item.variance_percentage, Decimal('-2.0'))
    
    def test_negative_quantity_validation(self):
        """Testa a validação de quantidade negativa"""
        item = InventoryCountItem(
            inventory_count=self.inventory_count,
            material=self.material,
            system_quantity=Decimal('-10.0'),  # Quantidade negativa
            counted_quantity=Decimal('0.0'),
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            item.full_clean()