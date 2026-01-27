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
