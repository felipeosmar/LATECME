from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, date
from .models import ProductionOrder, Bin, Batch, BatchItem, BinHistory
from apps.materials.models import Material, MaterialCategory
from apps.inventory.models import Warehouse


User = get_user_model()


class ProductionOrderTestCase(TestCase):
    """Testes para o model ProductionOrder"""

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

    def test_create_production_order(self):
        """Testa a criação de uma ordem de produção"""
        production_order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='DRAFT',
            planned_start_date=timezone.now().date(),
            planned_end_date=timezone.now().date() + timedelta(days=7),
            responsible=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(production_order.material, self.material)
        self.assertEqual(production_order.planned_quantity, Decimal('100.0'))
        self.assertEqual(production_order.produced_quantity, Decimal('0.0'))
        self.assertEqual(production_order.status, 'DRAFT')
        self.assertIsNotNone(production_order.order_number)
        self.assertTrue(production_order.order_number.startswith('OP-'))
        self.assertTrue(production_order.is_active)

    def test_production_order_auto_number_generation(self):
        """Testa a geração automática do número da ordem"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        today = timezone.now().date()
        expected_prefix = f"OP-{today.strftime('%Y%m%d')}-"
        self.assertTrue(order.order_number.startswith(expected_prefix))

    def test_production_order_str_method(self):
        """Testa o método __str__ da ordem de produção"""
        order = ProductionOrder.objects.create(
            order_number='OP-20240101-001',
            material=self.material,
            planned_quantity=Decimal('100.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(str(order), f'OP-20240101-001 - {self.material.code}')

    def test_production_order_unique_order_number(self):
        """Testa a unicidade do número da ordem"""
        ProductionOrder.objects.create(
            order_number='OP-20240101-001',
            material=self.material,
            planned_quantity=Decimal('100.0'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(Exception):
            ProductionOrder.objects.create(
                order_number='OP-20240101-001',  # Número duplicado
                material=self.material,
                planned_quantity=Decimal('50.0'),
                created_by=self.user,
                updated_by=self.user
            )

    def test_completion_percentage_property(self):
        """Testa a propriedade completion_percentage"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            produced_quantity=Decimal('25.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(order.completion_percentage, Decimal('25.0'))

    def test_completion_percentage_zero_planned(self):
        """Testa completion_percentage quando planned_quantity é zero"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('0.0'),
            produced_quantity=Decimal('0.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(order.completion_percentage, Decimal('0.00'))

    def test_is_overdue_property_when_overdue(self):
        """Testa a propriedade is_overdue quando está atrasada"""
        past_date = timezone.now().date() - timedelta(days=5)
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='IN_PROGRESS',
            planned_end_date=past_date,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertTrue(order.is_overdue)

    def test_is_overdue_property_when_not_overdue(self):
        """Testa a propriedade is_overdue quando não está atrasada"""
        future_date = timezone.now().date() + timedelta(days=5)
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='IN_PROGRESS',
            planned_end_date=future_date,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertFalse(order.is_overdue)

    def test_is_overdue_property_when_completed(self):
        """Testa is_overdue quando ordem está concluída"""
        past_date = timezone.now().date() - timedelta(days=5)
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='COMPLETED',
            planned_end_date=past_date,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertFalse(order.is_overdue)

    def test_is_overdue_property_when_no_planned_end_date(self):
        """Testa is_overdue quando não há data fim planejada"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='IN_PROGRESS',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertFalse(order.is_overdue)

    def test_can_start_method_when_draft(self):
        """Testa o método can_start quando status é DRAFT"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertTrue(order.can_start())

    def test_can_start_method_when_planned(self):
        """Testa o método can_start quando status é PLANNED"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='PLANNED',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertTrue(order.can_start())

    def test_can_start_method_when_in_progress(self):
        """Testa can_start quando já está em andamento"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='IN_PROGRESS',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertFalse(order.can_start())

    def test_start_method_success(self):
        """Testa o método start com sucesso"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )

        result = order.start(user=self.user)
        order.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(order.status, 'IN_PROGRESS')
        self.assertIsNotNone(order.actual_start_date)
        self.assertEqual(order.updated_by, self.user)

    def test_start_method_failure_when_completed(self):
        """Testa start quando ordem já está concluída"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='COMPLETED',
            created_by=self.user,
            updated_by=self.user
        )

        result = order.start(user=self.user)

        self.assertFalse(result)
        self.assertEqual(order.status, 'COMPLETED')

    def test_complete_method_success(self):
        """Testa o método complete com sucesso"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='IN_PROGRESS',
            created_by=self.user,
            updated_by=self.user
        )

        result = order.complete(user=self.user)
        order.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(order.status, 'COMPLETED')
        self.assertIsNotNone(order.actual_end_date)
        self.assertEqual(order.updated_by, self.user)

    def test_complete_method_failure_when_draft(self):
        """Testa complete quando ordem não está em andamento"""
        order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )

        result = order.complete(user=self.user)

        self.assertFalse(result)
        self.assertEqual(order.status, 'DRAFT')

    def test_negative_planned_quantity_validation(self):
        """Testa a validação de quantidade planejada negativa"""
        order = ProductionOrder(
            material=self.material,
            planned_quantity=Decimal('-10.0'),  # Quantidade negativa
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_zero_planned_quantity_validation(self):
        """Testa a validação de quantidade planejada zero"""
        order = ProductionOrder(
            material=self.material,
            planned_quantity=Decimal('0.0'),  # Quantidade zero
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_negative_produced_quantity_validation(self):
        """Testa a validação de quantidade produzida negativa"""
        order = ProductionOrder(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            produced_quantity=Decimal('-5.0'),  # Quantidade negativa
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            order.full_clean()


class BinTestCase(TestCase):
    """Testes para o model Bin"""

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

    def test_create_bin(self):
        """Testa a criação de um contentor"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            status='EMPTY',
            capacity=Decimal('500.0'),
            location_code='A1-B2-C3',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(bin_obj.code, 'BIN001')
        self.assertEqual(bin_obj.warehouse, self.warehouse)
        self.assertEqual(bin_obj.status, 'EMPTY')
        self.assertEqual(bin_obj.capacity, Decimal('500.0'))
        self.assertEqual(bin_obj.location_code, 'A1-B2-C3')
        self.assertEqual(bin_obj.current_quantity, Decimal('0.000'))
        self.assertIsNone(bin_obj.current_material)
        self.assertTrue(bin_obj.is_active)

    def test_bin_auto_code_generation(self):
        """Testa a geração automática do código do contentor"""
        bin_obj = Bin.objects.create(
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertIsNotNone(bin_obj.code)
        self.assertTrue(bin_obj.code.startswith('BIN'))
        self.assertEqual(len(bin_obj.code), 8)  # BIN + 5 dígitos

    def test_bin_str_method_empty(self):
        """Testa o método __str__ do contentor vazio"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(str(bin_obj), 'BIN001 (Vazio)')

    def test_bin_str_method_loaded(self):
        """Testa o método __str__ do contentor carregado"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('100.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(str(bin_obj), 'BIN001 (100.0 kg de AL7075)')

    def test_bin_unique_together_warehouse_code(self):
        """Testa a unicidade de código por armazém"""
        Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(Exception):
            Bin.objects.create(
                code='BIN001',  # Código duplicado no mesmo armazém
                warehouse=self.warehouse,
                created_by=self.user,
                updated_by=self.user
            )

    def test_is_empty_property_when_empty(self):
        """Testa a propriedade is_empty quando está vazio"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertTrue(bin_obj.is_empty)

    def test_is_empty_property_when_no_material(self):
        """Testa a propriedade is_empty quando não tem material"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_quantity=Decimal('0.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertTrue(bin_obj.is_empty)

    def test_is_loaded_property_when_loaded(self):
        """Testa a propriedade is_loaded quando está carregado"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('100.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertTrue(bin_obj.is_loaded)
        self.assertFalse(bin_obj.is_empty)

    def test_clean_validation_quantity_without_material(self):
        """Testa validação de quantidade sem material"""
        bin_obj = Bin(
            code='BIN001',
            warehouse=self.warehouse,
            current_quantity=Decimal('100.0'),  # Quantidade sem material
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            bin_obj.full_clean()

    def test_load_material_into_empty_bin(self):
        """Testa carregar material em contentor vazio"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        result = bin_obj.load_material(
            material=self.material,
            quantity=Decimal('50.0'),
            supplier_batch='LOTE-001',
            certificate='CERT-001',
            user=self.user
        )

        self.assertTrue(result)
        bin_obj.refresh_from_db()
        self.assertEqual(bin_obj.current_material, self.material)
        self.assertEqual(bin_obj.current_quantity, Decimal('50.0'))
        self.assertEqual(bin_obj.current_supplier_batch, 'LOTE-001')
        self.assertEqual(bin_obj.current_certificate, 'CERT-001')
        self.assertEqual(bin_obj.status, 'LOADED')

        # Verificar se criou entrada no histórico
        history_count = BinHistory.objects.filter(bin=bin_obj).count()
        self.assertEqual(history_count, 1)

    def test_load_material_into_same_material_bin(self):
        """Testa carregar mais material do mesmo tipo"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('50.0'),
            current_supplier_batch='LOTE-001',
            current_certificate='CERT-001',
            created_by=self.user,
            updated_by=self.user
        )

        bin_obj.load_material(
            material=self.material,
            quantity=Decimal('30.0'),
            user=self.user
        )

        bin_obj.refresh_from_db()
        self.assertEqual(bin_obj.current_quantity, Decimal('80.0'))
        self.assertEqual(bin_obj.current_supplier_batch, 'LOTE-001')

    def test_load_material_different_material_raises_error(self):
        """Testa erro ao carregar material diferente"""
        material2 = Material.objects.create(
            code='AL6061',
            name='Alumínio 6061',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.700'),
            created_by=self.user,
            updated_by=self.user
        )

        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            bin_obj.load_material(
                material=material2,  # Material diferente
                quantity=Decimal('30.0'),
                user=self.user
            )

    def test_unload_material_from_bin(self):
        """Testa descarregar material do contentor"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            status='LOADED',
            current_material=self.material,
            current_quantity=Decimal('100.0'),
            current_supplier_batch='LOTE-001',
            current_certificate='CERT-001',
            created_by=self.user,
            updated_by=self.user
        )

        result = bin_obj.unload_material(
            quantity=Decimal('30.0'),
            user=self.user,
            notes='Teste de descarga'
        )

        self.assertTrue(result)
        bin_obj.refresh_from_db()
        self.assertEqual(bin_obj.current_quantity, Decimal('70.0'))
        self.assertEqual(bin_obj.current_material, self.material)
        self.assertEqual(bin_obj.status, 'LOADED')

        # Verificar se criou entrada no histórico
        history = BinHistory.objects.filter(bin=bin_obj, movement_type='OUT').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.quantity, Decimal('30.0'))

    def test_unload_material_complete_empties_bin(self):
        """Testa descarregar toda quantidade esvazia o contentor"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('50.0'),
            current_supplier_batch='LOTE-001',
            created_by=self.user,
            updated_by=self.user
        )

        bin_obj.unload_material(
            quantity=Decimal('50.0'),
            user=self.user
        )

        bin_obj.refresh_from_db()
        self.assertEqual(bin_obj.current_quantity, Decimal('0.000'))
        self.assertIsNone(bin_obj.current_material)
        self.assertEqual(bin_obj.current_supplier_batch, '')
        self.assertEqual(bin_obj.status, 'EMPTY')
        self.assertTrue(bin_obj.is_empty)

    def test_unload_material_from_empty_bin_raises_error(self):
        """Testa erro ao descarregar de contentor vazio"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            bin_obj.unload_material(
                quantity=Decimal('10.0'),
                user=self.user
            )

    def test_unload_material_exceeds_quantity_raises_error(self):
        """Testa erro ao descarregar quantidade maior que disponível"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            bin_obj.unload_material(
                quantity=Decimal('100.0'),  # Maior que disponível
                user=self.user
            )

    def test_empty_bin(self):
        """Testa esvaziar contentor"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('75.0'),
            current_supplier_batch='LOTE-001',
            current_certificate='CERT-001',
            created_by=self.user,
            updated_by=self.user
        )

        result = bin_obj.empty(
            user=self.user,
            notes='Esvaziamento completo'
        )

        self.assertTrue(result)
        bin_obj.refresh_from_db()
        self.assertEqual(bin_obj.current_quantity, Decimal('0.000'))
        self.assertIsNone(bin_obj.current_material)
        self.assertEqual(bin_obj.current_supplier_batch, '')
        self.assertEqual(bin_obj.current_certificate, '')
        self.assertEqual(bin_obj.status, 'EMPTY')
        self.assertTrue(bin_obj.is_empty)

        # Verificar se criou entrada no histórico
        history = BinHistory.objects.filter(bin=bin_obj, movement_type='EMPTY').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.quantity, Decimal('75.0'))

    def test_empty_already_empty_bin(self):
        """Testa esvaziar contentor já vazio"""
        bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        result = bin_obj.empty(user=self.user)

        self.assertTrue(result)
        # Não deve criar histórico se já estava vazio
        history_count = BinHistory.objects.filter(bin=bin_obj).count()
        self.assertEqual(history_count, 0)


class BinHistoryTestCase(TestCase):
    """Testes para o model BinHistory"""

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

        self.bin_obj = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_bin_history(self):
        """Testa a criação de histórico de contentor"""
        history = BinHistory.objects.create(
            bin=self.bin_obj,
            movement_type='IN',
            material=self.material,
            quantity=Decimal('50.0'),
            supplier_batch='LOTE-001',
            certificate='CERT-001',
            performed_by=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(history.bin, self.bin_obj)
        self.assertEqual(history.movement_type, 'IN')
        self.assertEqual(history.material, self.material)
        self.assertEqual(history.quantity, Decimal('50.0'))
        self.assertEqual(history.supplier_batch, 'LOTE-001')
        self.assertEqual(history.certificate, 'CERT-001')
        self.assertEqual(history.performed_by, self.user)
        self.assertTrue(history.is_active)

    def test_bin_history_str_method(self):
        """Testa o método __str__ do histórico"""
        history = BinHistory.objects.create(
            bin=self.bin_obj,
            movement_type='IN',
            material=self.material,
            quantity=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(str(history), 'BIN001 - Entrada - 50.0 kg')

    def test_bin_history_created_by_load_material(self):
        """Testa criação de histórico ao carregar material"""
        self.bin_obj.load_material(
            material=self.material,
            quantity=Decimal('50.0'),
            supplier_batch='LOTE-001',
            certificate='CERT-001',
            user=self.user
        )

        history = BinHistory.objects.filter(
            bin=self.bin_obj,
            movement_type='IN'
        ).first()

        self.assertIsNotNone(history)
        self.assertEqual(history.material, self.material)
        self.assertEqual(history.quantity, Decimal('50.0'))
        self.assertEqual(history.supplier_batch, 'LOTE-001')
        self.assertEqual(history.certificate, 'CERT-001')

    def test_bin_history_created_by_unload_material(self):
        """Testa criação de histórico ao descarregar material"""
        # Primeiro, carregar material
        self.bin_obj.load_material(
            material=self.material,
            quantity=Decimal('100.0'),
            user=self.user
        )

        # Depois, descarregar
        self.bin_obj.unload_material(
            quantity=Decimal('40.0'),
            user=self.user,
            notes='Teste de descarga'
        )

        history_out = BinHistory.objects.filter(
            bin=self.bin_obj,
            movement_type='OUT'
        ).first()

        self.assertIsNotNone(history_out)
        self.assertEqual(history_out.quantity, Decimal('40.0'))
        self.assertEqual(history_out.notes, 'Teste de descarga')

    def test_bin_history_created_by_empty(self):
        """Testa criação de histórico ao esvaziar contentor"""
        # Primeiro, carregar material
        self.bin_obj.load_material(
            material=self.material,
            quantity=Decimal('75.0'),
            user=self.user
        )

        # Depois, esvaziar
        self.bin_obj.empty(
            user=self.user,
            notes='Esvaziamento completo'
        )

        history_empty = BinHistory.objects.filter(
            bin=self.bin_obj,
            movement_type='EMPTY'
        ).first()

        self.assertIsNotNone(history_empty)
        self.assertEqual(history_empty.quantity, Decimal('75.0'))
        self.assertEqual(history_empty.notes, 'Esvaziamento completo')

    def test_bin_history_multiple_operations(self):
        """Testa múltiplas operações e criação de histórico"""
        # Carregar
        self.bin_obj.load_material(
            material=self.material,
            quantity=Decimal('100.0'),
            user=self.user
        )

        # Descarregar parcialmente
        self.bin_obj.unload_material(
            quantity=Decimal('30.0'),
            user=self.user
        )

        # Carregar mais
        self.bin_obj.load_material(
            material=self.material,
            quantity=Decimal('20.0'),
            user=self.user
        )

        # Verificar que temos 3 entradas no histórico
        history_count = BinHistory.objects.filter(bin=self.bin_obj).count()
        self.assertEqual(history_count, 3)

        # Verificar tipos de movimentação
        in_count = BinHistory.objects.filter(
            bin=self.bin_obj,
            movement_type='IN'
        ).count()
        out_count = BinHistory.objects.filter(
            bin=self.bin_obj,
            movement_type='OUT'
        ).count()

        self.assertEqual(in_count, 2)
        self.assertEqual(out_count, 1)

    def test_bin_history_movement_types(self):
        """Testa todos os tipos de movimentação"""
        movement_types = ['IN', 'OUT', 'EMPTY', 'TRANSFER', 'ADJUSTMENT']

        for movement_type in movement_types:
            history = BinHistory.objects.create(
                bin=self.bin_obj,
                movement_type=movement_type,
                material=self.material,
                quantity=Decimal('10.0'),
                created_by=self.user,
                updated_by=self.user
            )
            self.assertEqual(history.movement_type, movement_type)

    def test_bin_history_with_batch(self):
        """Testa histórico com referência a batelada"""
        production_order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            created_by=self.user,
            updated_by=self.user
        )

        batch = Batch.objects.create(
            production_order=production_order,
            material=self.material,
            target_quantity=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        history = BinHistory.objects.create(
            bin=self.bin_obj,
            movement_type='OUT',
            material=self.material,
            quantity=Decimal('25.0'),
            batch=batch,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(history.batch, batch)
        self.assertEqual(history.movement_type, 'OUT')

    def test_bin_history_ordering(self):
        """Testa ordenação do histórico por data de criação decrescente"""
        # Criar múltiplas entradas
        history1 = BinHistory.objects.create(
            bin=self.bin_obj,
            movement_type='IN',
            material=self.material,
            quantity=Decimal('10.0'),
            created_by=self.user,
            updated_by=self.user
        )

        history2 = BinHistory.objects.create(
            bin=self.bin_obj,
            movement_type='IN',
            material=self.material,
            quantity=Decimal('20.0'),
            created_by=self.user,
            updated_by=self.user
        )

        history3 = BinHistory.objects.create(
            bin=self.bin_obj,
            movement_type='OUT',
            material=self.material,
            quantity=Decimal('5.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Verificar ordenação (mais recente primeiro)
        histories = list(BinHistory.objects.all())
        self.assertEqual(histories[0].id, history3.id)
        self.assertEqual(histories[1].id, history2.id)
        self.assertEqual(histories[2].id, history1.id)


class BatchTestCase(TestCase):
    """Testes para o model Batch"""

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

        self.production_order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='PLANNED',
            created_by=self.user,
            updated_by=self.user
        )

        self.bin = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('50.0'),
            current_supplier_batch='LOT123',
            current_certificate='CERT456',
            status='LOADED',
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_batch(self):
        """Testa a criação de uma batelada"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(batch.production_order, self.production_order)
        self.assertEqual(batch.material, self.material)
        self.assertEqual(batch.target_quantity, Decimal('30.0'))
        self.assertEqual(batch.actual_quantity, Decimal('0.0'))
        self.assertEqual(batch.status, 'PREPARATION')
        self.assertIsNotNone(batch.batch_number)
        self.assertTrue(batch.batch_number.startswith('BAT-'))
        self.assertTrue(batch.is_active)

    def test_batch_auto_number_generation(self):
        """Testa a geração automática do número da batelada"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            created_by=self.user,
            updated_by=self.user
        )

        today = timezone.now().date()
        expected_prefix = f"BAT-{today.strftime('%Y%m%d')}-"
        self.assertTrue(batch.batch_number.startswith(expected_prefix))

    def test_batch_str_method(self):
        """Testa o método __str__ da batelada"""
        batch = Batch.objects.create(
            batch_number='BAT-20240101-001',
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            actual_quantity=Decimal('25.5'),
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f'BAT-20240101-001 - {self.material.code} (25.5 kg)'
        self.assertEqual(str(batch), expected_str)

    def test_batch_unique_batch_number(self):
        """Testa a unicidade do número da batelada"""
        Batch.objects.create(
            batch_number='BAT-20240101-001',
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(Exception):
            Batch.objects.create(
                batch_number='BAT-20240101-001',  # Número duplicado
                production_order=self.production_order,
                material=self.material,
                target_quantity=Decimal('20.0'),
                created_by=self.user,
                updated_by=self.user
            )

    def test_batch_auto_set_material_from_production_order(self):
        """Testa definição automática do material da ordem de produção"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            target_quantity=Decimal('30.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(batch.material, self.production_order.material)

    def test_batch_material_validation(self):
        """Testa validação de material diferente da ordem de produção"""
        # Criar outro material
        other_material = Material.objects.create(
            code='AL6061',
            name='Alumínio 6061',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.700'),
            created_by=self.user,
            updated_by=self.user
        )

        batch = Batch(
            production_order=self.production_order,
            material=other_material,  # Material diferente
            target_quantity=Decimal('30.0'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.full_clean()

    def test_quantity_variance_property(self):
        """Testa a propriedade quantity_variance"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            actual_quantity=Decimal('32.5'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(batch.quantity_variance, Decimal('2.5'))

    def test_quantity_variance_negative(self):
        """Testa quantity_variance quando real é menor que alvo"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            actual_quantity=Decimal('28.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(batch.quantity_variance, Decimal('-2.0'))

    def test_is_complete_property_when_complete(self):
        """Testa is_complete quando quantidade real >= alvo"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            actual_quantity=Decimal('30.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertTrue(batch.is_complete)

    def test_is_complete_property_when_not_complete(self):
        """Testa is_complete quando quantidade real < alvo"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            actual_quantity=Decimal('25.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertFalse(batch.is_complete)

    def test_add_bin_material(self):
        """Testa adicionar material de um contentor à batelada"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',
            created_by=self.user,
            updated_by=self.user
        )

        batch_item = batch.add_bin_material(
            bin_obj=self.bin,
            quantity=Decimal('20.0'),
            user=self.user
        )

        # Verificar que o item foi criado
        self.assertIsNotNone(batch_item)
        self.assertEqual(batch_item.batch, batch)
        self.assertEqual(batch_item.bin, self.bin)
        self.assertEqual(batch_item.quantity, Decimal('20.0'))

        # Verificar que a quantidade foi atualizada na batelada
        batch.refresh_from_db()
        self.assertEqual(batch.actual_quantity, Decimal('20.0'))

        # Verificar que o contentor foi descarregado
        self.bin.refresh_from_db()
        self.assertEqual(self.bin.current_quantity, Decimal('30.0'))

    def test_add_bin_material_wrong_status(self):
        """Testa adicionar material quando batelada não está em preparação"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='COMPLETED',  # Status errado
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.add_bin_material(
                bin_obj=self.bin,
                quantity=Decimal('20.0'),
                user=self.user
            )

    def test_add_bin_material_empty_bin(self):
        """Testa adicionar material de contentor vazio"""
        empty_bin = Bin.objects.create(
            code='BIN002',
            warehouse=self.warehouse,
            status='EMPTY',
            created_by=self.user,
            updated_by=self.user
        )

        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.add_bin_material(
                bin_obj=empty_bin,
                quantity=Decimal('20.0'),
                user=self.user
            )

    def test_add_bin_material_wrong_material(self):
        """Testa adicionar material de contentor com material diferente"""
        # Criar outro material
        other_material = Material.objects.create(
            code='AL6061',
            name='Alumínio 6061',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.700'),
            created_by=self.user,
            updated_by=self.user
        )

        # Contentor com material diferente
        other_bin = Bin.objects.create(
            code='BIN002',
            warehouse=self.warehouse,
            current_material=other_material,
            current_quantity=Decimal('40.0'),
            status='LOADED',
            created_by=self.user,
            updated_by=self.user
        )

        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.add_bin_material(
                bin_obj=other_bin,
                quantity=Decimal('20.0'),
                user=self.user
            )

    def test_add_bin_material_insufficient_quantity(self):
        """Testa adicionar quantidade maior que disponível no contentor"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.add_bin_material(
                bin_obj=self.bin,
                quantity=Decimal('100.0'),  # Mais que disponível
                user=self.user
            )

    def test_mark_ready(self):
        """Testa marcar batelada como pronta"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',
            created_by=self.user,
            updated_by=self.user
        )

        # Adicionar material primeiro
        batch.add_bin_material(
            bin_obj=self.bin,
            quantity=Decimal('25.0'),
            user=self.user
        )

        result = batch.mark_ready(user=self.user)

        self.assertTrue(result)
        batch.refresh_from_db()
        self.assertEqual(batch.status, 'READY')
        self.assertIsNotNone(batch.preparation_date)
        self.assertEqual(batch.prepared_by, self.user)

    def test_mark_ready_wrong_status(self):
        """Testa mark_ready quando status não é PREPARATION"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='READY',  # Status errado
            actual_quantity=Decimal('25.0'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.mark_ready(user=self.user)

    def test_mark_ready_no_material(self):
        """Testa mark_ready quando não há material coletado"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.mark_ready(user=self.user)

    def test_start_production(self):
        """Testa iniciar produção com a batelada"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='READY',
            actual_quantity=Decimal('25.0'),
            created_by=self.user,
            updated_by=self.user
        )

        result = batch.start_production(user=self.user)

        self.assertTrue(result)
        batch.refresh_from_db()
        self.assertEqual(batch.status, 'IN_PRODUCTION')
        self.assertIsNotNone(batch.production_start_date)

        # Verificar se a ordem de produção foi iniciada
        self.production_order.refresh_from_db()
        self.assertEqual(self.production_order.status, 'IN_PROGRESS')

    def test_start_production_wrong_status(self):
        """Testa start_production quando status não é READY"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',  # Status errado
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.start_production(user=self.user)

    def test_complete_batch(self):
        """Testa concluir a batelada"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='IN_PRODUCTION',
            actual_quantity=Decimal('28.0'),
            created_by=self.user,
            updated_by=self.user
        )

        initial_produced = self.production_order.produced_quantity

        result = batch.complete(user=self.user)

        self.assertTrue(result)
        batch.refresh_from_db()
        self.assertEqual(batch.status, 'COMPLETED')
        self.assertIsNotNone(batch.completion_date)

        # Verificar se a quantidade produzida foi atualizada na ordem
        self.production_order.refresh_from_db()
        expected_produced = initial_produced + Decimal('28.0')
        self.assertEqual(self.production_order.produced_quantity, expected_produced)

    def test_complete_batch_wrong_status(self):
        """Testa complete quando status não é IN_PRODUCTION"""
        batch = Batch.objects.create(
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='READY',  # Status errado
            actual_quantity=Decimal('28.0'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            batch.complete(user=self.user)


class BatchItemTestCase(TestCase):
    """Testes para o model BatchItem"""

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

        self.production_order = ProductionOrder.objects.create(
            material=self.material,
            planned_quantity=Decimal('100.0'),
            status='PLANNED',
            created_by=self.user,
            updated_by=self.user
        )

        self.batch = Batch.objects.create(
            batch_number='BAT-20240101-001',
            production_order=self.production_order,
            material=self.material,
            target_quantity=Decimal('30.0'),
            status='PREPARATION',
            created_by=self.user,
            updated_by=self.user
        )

        self.bin = Bin.objects.create(
            code='BIN001',
            warehouse=self.warehouse,
            current_material=self.material,
            current_quantity=Decimal('50.0'),
            current_supplier_batch='LOT123',
            current_certificate='CERT456',
            status='LOADED',
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_batch_item(self):
        """Testa a criação de um item da batelada"""
        batch_item = BatchItem.objects.create(
            batch=self.batch,
            bin=self.bin,
            material=self.material,
            quantity=Decimal('20.0'),
            supplier_batch='LOT123',
            certificate='CERT456',
            collected_by=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(batch_item.batch, self.batch)
        self.assertEqual(batch_item.bin, self.bin)
        self.assertEqual(batch_item.material, self.material)
        self.assertEqual(batch_item.quantity, Decimal('20.0'))
        self.assertEqual(batch_item.supplier_batch, 'LOT123')
        self.assertEqual(batch_item.certificate, 'CERT456')
        self.assertEqual(batch_item.collected_by, self.user)
        self.assertIsNotNone(batch_item.collected_at)
        self.assertTrue(batch_item.is_active)

    def test_batch_item_str_method(self):
        """Testa o método __str__ do item da batelada"""
        batch_item = BatchItem.objects.create(
            batch=self.batch,
            bin=self.bin,
            material=self.material,
            quantity=Decimal('20.0'),
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f"{self.batch.batch_number} - {self.bin.code} - 20.0 kg"
        self.assertEqual(str(batch_item), expected_str)

    def test_batch_item_str_method_no_bin(self):
        """Testa __str__ quando bin é None"""
        batch_item = BatchItem.objects.create(
            batch=self.batch,
            bin=None,
            material=self.material,
            quantity=Decimal('20.0'),
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f"{self.batch.batch_number} - N/A - 20.0 kg"
        self.assertEqual(str(batch_item), expected_str)

    def test_batch_item_ordering(self):
        """Testa ordenação dos itens por data de coleta"""
        item1 = BatchItem.objects.create(
            batch=self.batch,
            bin=self.bin,
            material=self.material,
            quantity=Decimal('10.0'),
            created_by=self.user,
            updated_by=self.user
        )

        item2 = BatchItem.objects.create(
            batch=self.batch,
            bin=self.bin,
            material=self.material,
            quantity=Decimal('15.0'),
            created_by=self.user,
            updated_by=self.user
        )

        items = list(BatchItem.objects.all())
        self.assertEqual(items[0], item1)  # Mais antigo primeiro
        self.assertEqual(items[1], item2)

    def test_batch_item_relationship_with_batch(self):
        """Testa relacionamento com Batch"""
        batch_item = BatchItem.objects.create(
            batch=self.batch,
            bin=self.bin,
            material=self.material,
            quantity=Decimal('20.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(self.batch.items.count(), 1)
        self.assertEqual(self.batch.items.first(), batch_item)

    def test_batch_item_relationship_with_bin(self):
        """Testa relacionamento com Bin"""
        batch_item = BatchItem.objects.create(
            batch=self.batch,
            bin=self.bin,
            material=self.material,
            quantity=Decimal('20.0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(self.bin.batch_items.count(), 1)
        self.assertEqual(self.bin.batch_items.first(), batch_item)
