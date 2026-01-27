from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from .models import PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem, Receiving, ReceivingItem
from apps.materials.models import Material, MaterialCategory, Supplier
from apps.inventory.models import Warehouse


User = get_user_model()


class PurchaseRequestTestCase(TestCase):
    """Testes para o model PurchaseRequest"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()

        self.approver = User.objects.create_user(
            username='approver',
            email='approver@example.com',
            password='testpass123'
        )
        self.approver.status = 'approved'
        self.approver.save()

        self.warehouse = Warehouse.objects.create(
            code='WH001',
            name='Armazém Principal',
            created_by=self.user,
            updated_by=self.user
        )

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

    def test_create_purchase_request(self):
        """Testa a criação de uma solicitação de compra"""
        pr = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            department='Produção',
            priority='HIGH',
            justification='Material necessário para produção urgente',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(pr.requester, self.user)
        self.assertEqual(pr.warehouse, self.warehouse)
        self.assertEqual(pr.department, 'Produção')
        self.assertEqual(pr.status, 'DRAFT')
        self.assertEqual(pr.priority, 'HIGH')
        self.assertTrue(pr.is_active)
        self.assertIsNotNone(pr.reference_number)
        self.assertTrue(pr.reference_number.startswith('SC'))

    def test_purchase_request_reference_number_generation(self):
        """Testa a geração automática do número de referência"""
        pr1 = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        pr2 = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(pr1.reference_number, 'SC00001')
        self.assertEqual(pr2.reference_number, 'SC00002')

    def test_purchase_request_unique_reference_number(self):
        """Testa a unicidade do número de referência"""
        PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        # Tentar criar com mesmo reference_number deve falhar
        with self.assertRaises(Exception):
            pr = PurchaseRequest(
                reference_number='SC00001',
                requester=self.user,
                warehouse=self.warehouse,
                created_by=self.user,
                updated_by=self.user
            )
            pr.save()

    def test_purchase_request_str(self):
        """Testa a representação em string da solicitação"""
        pr = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            status='PENDING',
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f"{pr.reference_number} - Aguardando Aprovacao"
        self.assertEqual(str(pr), expected_str)

    def test_purchase_request_total_value_property(self):
        """Testa a propriedade total_value"""
        pr = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        # Sem itens, total deve ser 0
        self.assertEqual(pr.total_value, 0)

        # Adicionar itens
        PurchaseRequestItem.objects.create(
            purchase_request=pr,
            material=self.material,
            quantity=Decimal('10.0'),
            estimated_unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        PurchaseRequestItem.objects.create(
            purchase_request=pr,
            material=self.material,
            quantity=Decimal('5.0'),
            estimated_unit_price=Decimal('60.00'),
            created_by=self.user,
            updated_by=self.user
        )

        # Total = (10 * 50) + (5 * 60) = 500 + 300 = 800
        self.assertEqual(pr.total_value, Decimal('800.00'))

    def test_purchase_request_can_approve_property(self):
        """Testa a propriedade can_approve"""
        pr = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )

        # DRAFT não pode aprovar
        self.assertFalse(pr.can_approve)

        # PENDING pode aprovar
        pr.status = 'PENDING'
        pr.save()
        self.assertTrue(pr.can_approve)

        # APPROVED não pode aprovar
        pr.status = 'APPROVED'
        pr.save()
        self.assertFalse(pr.can_approve)

    def test_purchase_request_can_edit_property(self):
        """Testa a propriedade can_edit"""
        pr = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )

        # DRAFT pode editar
        self.assertTrue(pr.can_edit)

        # PENDING pode editar
        pr.status = 'PENDING'
        pr.save()
        self.assertTrue(pr.can_edit)

        # APPROVED não pode editar
        pr.status = 'APPROVED'
        pr.save()
        self.assertFalse(pr.can_edit)

        # REJECTED não pode editar
        pr.status = 'REJECTED'
        pr.save()
        self.assertFalse(pr.can_edit)

    def test_purchase_request_approval_workflow(self):
        """Testa o fluxo de aprovação"""
        pr = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            status='PENDING',
            created_by=self.user,
            updated_by=self.user
        )

        # Aprovar
        pr.status = 'APPROVED'
        pr.approved_by = self.approver
        pr.approved_at = timezone.now()
        pr.save()

        self.assertEqual(pr.status, 'APPROVED')
        self.assertEqual(pr.approved_by, self.approver)
        self.assertIsNotNone(pr.approved_at)

    def test_purchase_request_required_date(self):
        """Testa a data necessária"""
        future_date = timezone.now().date() + timedelta(days=30)
        pr = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            required_date=future_date,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(pr.required_date, future_date)


class PurchaseRequestItemTestCase(TestCase):
    """Testes para o model PurchaseRequestItem"""

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

        self.purchase_request = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_purchase_request_item(self):
        """Testa a criação de um item de solicitação"""
        item = PurchaseRequestItem.objects.create(
            purchase_request=self.purchase_request,
            material=self.material,
            quantity=Decimal('10.5'),
            estimated_unit_price=Decimal('50.00'),
            preferred_supplier=self.supplier,
            notes='Material urgente',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(item.purchase_request, self.purchase_request)
        self.assertEqual(item.material, self.material)
        self.assertEqual(item.quantity, Decimal('10.5'))
        self.assertEqual(item.estimated_unit_price, Decimal('50.00'))
        self.assertEqual(item.preferred_supplier, self.supplier)
        self.assertEqual(item.notes, 'Material urgente')
        self.assertTrue(item.is_active)

    def test_purchase_request_item_str(self):
        """Testa a representação em string do item"""
        item = PurchaseRequestItem.objects.create(
            purchase_request=self.purchase_request,
            material=self.material,
            quantity=Decimal('10.5'),
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f"{self.material.code} - 10.5 kg"
        self.assertEqual(str(item), expected_str)

    def test_purchase_request_item_total_price_property(self):
        """Testa a propriedade total_price"""
        item = PurchaseRequestItem.objects.create(
            purchase_request=self.purchase_request,
            material=self.material,
            quantity=Decimal('10.0'),
            estimated_unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        # Total = 10 * 50 = 500
        self.assertEqual(item.total_price, Decimal('500.00'))

    def test_purchase_request_item_total_price_without_unit_price(self):
        """Testa total_price quando não há preço unitário"""
        item = PurchaseRequestItem.objects.create(
            purchase_request=self.purchase_request,
            material=self.material,
            quantity=Decimal('10.0'),
            estimated_unit_price=None,
            created_by=self.user,
            updated_by=self.user
        )

        # Sem preço unitário, total deve ser 0
        self.assertEqual(item.total_price, Decimal('0'))

    def test_purchase_request_item_quantity_validation(self):
        """Testa a validação de quantidade positiva"""
        item = PurchaseRequestItem(
            purchase_request=self.purchase_request,
            material=self.material,
            quantity=Decimal('0'),  # Quantidade inválida
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_purchase_request_item_negative_quantity_validation(self):
        """Testa a validação de quantidade negativa"""
        item = PurchaseRequestItem(
            purchase_request=self.purchase_request,
            material=self.material,
            quantity=Decimal('-5.0'),  # Quantidade negativa
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_purchase_request_item_without_supplier(self):
        """Testa item sem fornecedor preferencial"""
        item = PurchaseRequestItem.objects.create(
            purchase_request=self.purchase_request,
            material=self.material,
            quantity=Decimal('10.0'),
            estimated_unit_price=Decimal('50.00'),
            preferred_supplier=None,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertIsNone(item.preferred_supplier)
        self.assertEqual(item.total_price, Decimal('500.00'))

    def test_multiple_items_in_purchase_request(self):
        """Testa múltiplos itens em uma solicitação"""
        item1 = PurchaseRequestItem.objects.create(
            purchase_request=self.purchase_request,
            material=self.material,
            quantity=Decimal('10.0'),
            estimated_unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        material2 = Material.objects.create(
            code='AL6061',
            name='Alumínio 6061',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.700'),
            created_by=self.user,
            updated_by=self.user
        )

        item2 = PurchaseRequestItem.objects.create(
            purchase_request=self.purchase_request,
            material=material2,
            quantity=Decimal('5.0'),
            estimated_unit_price=Decimal('40.00'),
            created_by=self.user,
            updated_by=self.user
        )

        # Verificar que ambos os itens estão na solicitação
        self.assertEqual(self.purchase_request.items.count(), 2)
        self.assertIn(item1, self.purchase_request.items.all())
        self.assertIn(item2, self.purchase_request.items.all())
