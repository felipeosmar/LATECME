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
