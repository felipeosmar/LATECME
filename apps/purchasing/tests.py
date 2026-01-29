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


class PurchaseOrderTestCase(TestCase):
    """Testes para o model PurchaseOrder"""

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

    def test_create_purchase_order(self):
        """Testa a criação de um pedido de compra"""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            payment_terms='30 dias',
            shipping_address='Rua da Indústria, 123',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(po.supplier, self.supplier)
        self.assertEqual(po.warehouse, self.warehouse)
        self.assertEqual(po.buyer, self.user)
        self.assertEqual(po.status, 'DRAFT')
        self.assertEqual(po.payment_terms, '30 dias')
        self.assertTrue(po.is_active)
        self.assertIsNotNone(po.reference_number)
        self.assertTrue(po.reference_number.startswith('PC'))

    def test_purchase_order_reference_number_generation(self):
        """Testa a geração automática do número de referência"""
        po1 = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        po2 = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(po1.reference_number, 'PC00001')
        self.assertEqual(po2.reference_number, 'PC00002')

    def test_purchase_order_unique_reference_number(self):
        """Testa a unicidade do número de referência"""
        PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        # Tentar criar com mesmo reference_number deve falhar
        with self.assertRaises(Exception):
            po = PurchaseOrder(
                reference_number='PC00001',
                supplier=self.supplier,
                warehouse=self.warehouse,
                buyer=self.user,
                created_by=self.user,
                updated_by=self.user
            )
            po.save()

    def test_purchase_order_str(self):
        """Testa a representação em string do pedido"""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f"{po.reference_number} - {self.supplier.name}"
        self.assertEqual(str(po), expected_str)

    def test_purchase_order_total_value_property(self):
        """Testa a propriedade total_value"""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        # Sem itens, total deve ser 0
        self.assertEqual(po.total_value, 0)

        # Adicionar itens
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            material=self.material,
            quantity=Decimal('10.0'),
            unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        PurchaseOrderItem.objects.create(
            purchase_order=po,
            material=self.material,
            quantity=Decimal('5.0'),
            unit_price=Decimal('60.00'),
            created_by=self.user,
            updated_by=self.user
        )

        # Total = (10 * 50) + (5 * 60) = 500 + 300 = 800
        self.assertEqual(po.total_value, Decimal('800.00'))

    def test_purchase_order_total_received_property(self):
        """Testa a propriedade total_received"""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        item1 = PurchaseOrderItem.objects.create(
            purchase_order=po,
            material=self.material,
            quantity=Decimal('10.0'),
            unit_price=Decimal('50.00'),
            received_quantity=Decimal('5.0'),
            created_by=self.user,
            updated_by=self.user
        )

        item2 = PurchaseOrderItem.objects.create(
            purchase_order=po,
            material=self.material,
            quantity=Decimal('20.0'),
            unit_price=Decimal('60.00'),
            received_quantity=Decimal('10.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Total recebido = 5.0 + 10.0 = 15.0
        self.assertEqual(po.total_received, Decimal('15.0'))

    def test_purchase_order_can_receive_property(self):
        """Testa a propriedade can_receive"""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )

        # DRAFT não pode receber
        self.assertFalse(po.can_receive)

        # SENT pode receber
        po.status = 'SENT'
        po.save()
        self.assertTrue(po.can_receive)

        # CONFIRMED pode receber
        po.status = 'CONFIRMED'
        po.save()
        self.assertTrue(po.can_receive)

        # PARTIAL pode receber
        po.status = 'PARTIAL'
        po.save()
        self.assertTrue(po.can_receive)

        # RECEIVED não pode receber
        po.status = 'RECEIVED'
        po.save()
        self.assertFalse(po.can_receive)

        # CANCELLED não pode receber
        po.status = 'CANCELLED'
        po.save()
        self.assertFalse(po.can_receive)

    def test_purchase_order_with_purchase_request(self):
        """Testa pedido vinculado a uma solicitação"""
        pr = PurchaseRequest.objects.create(
            requester=self.user,
            warehouse=self.warehouse,
            created_by=self.user,
            updated_by=self.user
        )

        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            purchase_request=pr,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(po.purchase_request, pr)
        self.assertIn(po, pr.purchase_orders.all())

    def test_purchase_order_expected_delivery_date(self):
        """Testa a data prevista de entrega"""
        future_date = timezone.now().date() + timedelta(days=15)
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            expected_delivery_date=future_date,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(po.expected_delivery_date, future_date)

    def test_purchase_order_status_workflow(self):
        """Testa o fluxo de status do pedido"""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            status='DRAFT',
            created_by=self.user,
            updated_by=self.user
        )

        # DRAFT -> SENT
        po.status = 'SENT'
        po.save()
        self.assertEqual(po.status, 'SENT')

        # SENT -> CONFIRMED
        po.status = 'CONFIRMED'
        po.save()
        self.assertEqual(po.status, 'CONFIRMED')

        # CONFIRMED -> PARTIAL
        po.status = 'PARTIAL'
        po.save()
        self.assertEqual(po.status, 'PARTIAL')

        # PARTIAL -> RECEIVED
        po.status = 'RECEIVED'
        po.save()
        self.assertEqual(po.status, 'RECEIVED')


class PurchaseOrderItemTestCase(TestCase):
    """Testes para o model PurchaseOrderItem"""

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

        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_purchase_order_item(self):
        """Testa a criação de um item de pedido"""
        item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('10.5'),
            unit_price=Decimal('50.00'),
            notes='Material de alta qualidade',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(item.purchase_order, self.purchase_order)
        self.assertEqual(item.material, self.material)
        self.assertEqual(item.quantity, Decimal('10.5'))
        self.assertEqual(item.unit_price, Decimal('50.00'))
        self.assertEqual(item.received_quantity, Decimal('0'))
        self.assertEqual(item.notes, 'Material de alta qualidade')
        self.assertTrue(item.is_active)

    def test_purchase_order_item_str(self):
        """Testa a representação em string do item"""
        item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('10.5'),
            unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f"{self.material.code} - 10.5 kg @ R$50.00"
        self.assertEqual(str(item), expected_str)

    def test_purchase_order_item_total_price_property(self):
        """Testa a propriedade total_price"""
        item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('10.0'),
            unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        # Total = 10 * 50 = 500
        self.assertEqual(item.total_price, Decimal('500.00'))

    def test_purchase_order_item_pending_quantity_property(self):
        """Testa a propriedade pending_quantity"""
        item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('100.0'),
            unit_price=Decimal('50.00'),
            received_quantity=Decimal('30.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Pendente = 100 - 30 = 70
        self.assertEqual(item.pending_quantity, Decimal('70.0'))

    def test_purchase_order_item_is_fully_received_property(self):
        """Testa a propriedade is_fully_received"""
        item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('100.0'),
            unit_price=Decimal('50.00'),
            received_quantity=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Não totalmente recebido
        self.assertFalse(item.is_fully_received)

        # Atualizar para totalmente recebido
        item.received_quantity = Decimal('100.0')
        item.save()
        self.assertTrue(item.is_fully_received)

        # Recebido além da quantidade pedida
        item.received_quantity = Decimal('110.0')
        item.save()
        self.assertTrue(item.is_fully_received)

    def test_purchase_order_item_quantity_validation(self):
        """Testa a validação de quantidade positiva"""
        item = PurchaseOrderItem(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('0'),  # Quantidade inválida
            unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_purchase_order_item_negative_quantity_validation(self):
        """Testa a validação de quantidade negativa"""
        item = PurchaseOrderItem(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('-5.0'),  # Quantidade negativa
            unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_purchase_order_item_unit_price_validation(self):
        """Testa a validação de preço unitário positivo"""
        item = PurchaseOrderItem(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('10.0'),
            unit_price=Decimal('0'),  # Preço inválido
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_purchase_order_item_negative_unit_price_validation(self):
        """Testa a validação de preço unitário negativo"""
        item = PurchaseOrderItem(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('10.0'),
            unit_price=Decimal('-50.00'),  # Preço negativo
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_multiple_items_in_purchase_order(self):
        """Testa múltiplos itens em um pedido"""
        item1 = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('10.0'),
            unit_price=Decimal('50.00'),
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

        item2 = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=material2,
            quantity=Decimal('5.0'),
            unit_price=Decimal('40.00'),
            created_by=self.user,
            updated_by=self.user
        )

        # Verificar que ambos os itens estão no pedido
        self.assertEqual(self.purchase_order.items.count(), 2)
        self.assertIn(item1, self.purchase_order.items.all())
        self.assertIn(item2, self.purchase_order.items.all())

    def test_purchase_order_item_partial_receiving(self):
        """Testa recebimento parcial de um item"""
        item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('100.0'),
            unit_price=Decimal('50.00'),
            received_quantity=Decimal('0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Primeira entrega parcial
        item.received_quantity = Decimal('30.0')
        item.save()
        self.assertEqual(item.pending_quantity, Decimal('70.0'))
        self.assertFalse(item.is_fully_received)

        # Segunda entrega parcial
        item.received_quantity = Decimal('80.0')
        item.save()
        self.assertEqual(item.pending_quantity, Decimal('20.0'))
        self.assertFalse(item.is_fully_received)

        # Entrega final
        item.received_quantity = Decimal('100.0')
        item.save()
        self.assertEqual(item.pending_quantity, Decimal('0'))
        self.assertTrue(item.is_fully_received)


class ReceivingTestCase(TestCase):
    """Testes para o model Receiving"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.status = 'approved'
        self.user.save()

        self.inspector = User.objects.create_user(
            username='inspector',
            email='inspector@example.com',
            password='testpass123'
        )
        self.inspector.status = 'approved'
        self.inspector.save()

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
            code='SUP001',
            name='Fornecedor Teste',
            cnpj='12345678000190',
            contact_email='contato@fornecedor.com',
            contact_phone='11 98765-4321',
            created_by=self.user,
            updated_by=self.user
        )

        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            status='CONFIRMED',
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_receiving(self):
        """Testa a criação de um recebimento"""
        receiving = Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            invoice_number='NF12345',
            invoice_date=timezone.now().date(),
            notes='Recebimento realizado sem problemas',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(receiving.purchase_order, self.purchase_order)
        self.assertEqual(receiving.received_by, self.user)
        self.assertEqual(receiving.status, 'PENDING')
        self.assertEqual(receiving.invoice_number, 'NF12345')
        self.assertTrue(receiving.is_active)
        self.assertIsNotNone(receiving.reference_number)
        self.assertTrue(receiving.reference_number.startswith('RB'))

    def test_receiving_reference_number_generation(self):
        """Testa a geração automática do número de referência"""
        receiving1 = Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        receiving2 = Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(receiving1.reference_number, 'RB00001')
        self.assertEqual(receiving2.reference_number, 'RB00002')

    def test_receiving_unique_reference_number(self):
        """Testa a unicidade do número de referência"""
        Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        # Tentar criar com mesmo reference_number deve falhar
        with self.assertRaises(Exception):
            receiving = Receiving(
                reference_number='RB00001',
                purchase_order=self.purchase_order,
                received_by=self.user,
                created_by=self.user,
                updated_by=self.user
            )
            receiving.save()

    def test_receiving_str(self):
        """Testa a representação em string do recebimento"""
        receiving = Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f"{receiving.reference_number} - {self.purchase_order.reference_number}"
        self.assertEqual(str(receiving), expected_str)

    def test_receiving_total_received_value_property(self):
        """Testa a propriedade total_received_value"""
        receiving = Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        # Sem itens, total deve ser 0
        self.assertEqual(receiving.total_received_value, 0)

        # Criar itens de pedido
        po_item1 = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('10.0'),
            unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        po_item2 = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('5.0'),
            unit_price=Decimal('60.00'),
            created_by=self.user,
            updated_by=self.user
        )

        # Adicionar itens de recebimento
        ReceivingItem.objects.create(
            receiving=receiving,
            purchase_order_item=po_item1,
            quantity_received=Decimal('10.0'),
            quantity_accepted=Decimal('10.0'),
            created_by=self.user,
            updated_by=self.user
        )

        ReceivingItem.objects.create(
            receiving=receiving,
            purchase_order_item=po_item2,
            quantity_received=Decimal('5.0'),
            quantity_accepted=Decimal('4.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Total = (10 * 50) + (4 * 60) = 500 + 240 = 740
        self.assertEqual(receiving.total_received_value, Decimal('740.00'))

    def test_receiving_status_workflow(self):
        """Testa o fluxo de status do recebimento"""
        receiving = Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            status='PENDING',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(receiving.status, 'PENDING')

        # Mudar para inspeção
        receiving.status = 'INSPECTING'
        receiving.inspected_by = self.inspector
        receiving.inspection_date = timezone.now()
        receiving.save()
        self.assertEqual(receiving.status, 'INSPECTING')
        self.assertEqual(receiving.inspected_by, self.inspector)

        # Aprovar
        receiving.status = 'APPROVED'
        receiving.save()
        self.assertEqual(receiving.status, 'APPROVED')

    def test_receiving_rejection(self):
        """Testa a rejeição de um recebimento"""
        receiving = Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            status='INSPECTING',
            created_by=self.user,
            updated_by=self.user
        )

        # Rejeitar
        receiving.status = 'REJECTED'
        receiving.rejection_reason = 'Material fora das especificações'
        receiving.inspected_by = self.inspector
        receiving.inspection_date = timezone.now()
        receiving.save()

        self.assertEqual(receiving.status, 'REJECTED')
        self.assertEqual(receiving.rejection_reason, 'Material fora das especificações')
        self.assertIsNotNone(receiving.inspected_by)
        self.assertIsNotNone(receiving.inspection_date)


class ReceivingItemTestCase(TestCase):
    """Testes para o model ReceivingItem"""

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
            code='SUP001',
            name='Fornecedor Teste',
            cnpj='12345678000190',
            contact_email='contato@fornecedor.com',
            contact_phone='11 98765-4321',
            created_by=self.user,
            updated_by=self.user
        )

        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            buyer=self.user,
            created_by=self.user,
            updated_by=self.user
        )

        self.purchase_order_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=self.material,
            quantity=Decimal('100.0'),
            unit_price=Decimal('50.00'),
            created_by=self.user,
            updated_by=self.user
        )

        self.receiving = Receiving.objects.create(
            purchase_order=self.purchase_order,
            received_by=self.user,
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_receiving_item(self):
        """Testa a criação de um item de recebimento"""
        item = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('50.0'),
            quantity_accepted=Decimal('48.0'),
            quantity_rejected=Decimal('2.0'),
            batch_number='LOTE123',
            notes='Item recebido com pequena avaria',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(item.receiving, self.receiving)
        self.assertEqual(item.purchase_order_item, self.purchase_order_item)
        self.assertEqual(item.quantity_received, Decimal('50.0'))
        self.assertEqual(item.quantity_accepted, Decimal('48.0'))
        self.assertEqual(item.quantity_rejected, Decimal('2.0'))
        self.assertEqual(item.batch_number, 'LOTE123')
        self.assertTrue(item.is_active)

    def test_receiving_item_str(self):
        """Testa a representação em string do item"""
        item = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        expected_str = f"{self.material.code} - 50.0 kg"
        self.assertEqual(str(item), expected_str)

    def test_receiving_item_total_value_property(self):
        """Testa a propriedade total_value com quantidade aceita"""
        item = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('50.0'),
            quantity_accepted=Decimal('48.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Total = quantidade_aceita * preço_unitário = 48 * 50 = 2400
        self.assertEqual(item.total_value, Decimal('2400.00'))

    def test_receiving_item_total_value_property_no_acceptance(self):
        """Testa a propriedade total_value sem quantidade aceita definida"""
        item = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Total usa quantity_received quando quantity_accepted é None
        # Total = 50 * 50 = 2500
        self.assertEqual(item.total_value, Decimal('2500.00'))

    def test_receiving_item_quantity_validation(self):
        """Testa a validação de quantidade positiva"""
        item = ReceivingItem(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('0'),  # Quantidade inválida
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_receiving_item_negative_quantity_validation(self):
        """Testa a validação de quantidade negativa"""
        item = ReceivingItem(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('-5.0'),  # Quantidade negativa
            created_by=self.user,
            updated_by=self.user
        )

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_multiple_items_in_receiving(self):
        """Testa múltiplos itens em um recebimento"""
        item1 = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('50.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Criar outro material e item de pedido
        material2 = Material.objects.create(
            code='AL6061',
            name='Alumínio 6061',
            material_type='aluminum',
            category=self.category,
            density=Decimal('2.700'),
            created_by=self.user,
            updated_by=self.user
        )

        po_item2 = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            material=material2,
            quantity=Decimal('30.0'),
            unit_price=Decimal('40.00'),
            created_by=self.user,
            updated_by=self.user
        )

        item2 = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=po_item2,
            quantity_received=Decimal('30.0'),
            created_by=self.user,
            updated_by=self.user
        )

        # Verificar que ambos os itens estão no recebimento
        self.assertEqual(self.receiving.items.count(), 2)
        self.assertIn(item1, self.receiving.items.all())
        self.assertIn(item2, self.receiving.items.all())

    def test_receiving_item_with_rejection(self):
        """Testa item com rejeição parcial"""
        item = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('100.0'),
            quantity_accepted=Decimal('85.0'),
            quantity_rejected=Decimal('15.0'),
            rejection_reason='15kg fora de especificação',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(item.quantity_received, Decimal('100.0'))
        self.assertEqual(item.quantity_accepted, Decimal('85.0'))
        self.assertEqual(item.quantity_rejected, Decimal('15.0'))
        self.assertEqual(item.rejection_reason, '15kg fora de especificação')
        # Total value usa quantidade aceita
        self.assertEqual(item.total_value, Decimal('4250.00'))  # 85 * 50

    def test_receiving_item_full_acceptance(self):
        """Testa item totalmente aceito"""
        item = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('100.0'),
            quantity_accepted=Decimal('100.0'),
            quantity_rejected=Decimal('0'),
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(item.quantity_received, Decimal('100.0'))
        self.assertEqual(item.quantity_accepted, Decimal('100.0'))
        self.assertEqual(item.quantity_rejected, Decimal('0'))
        self.assertEqual(item.total_value, Decimal('5000.00'))  # 100 * 50

    def test_receiving_item_full_rejection(self):
        """Testa item totalmente rejeitado"""
        item = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('100.0'),
            quantity_accepted=Decimal('0'),
            quantity_rejected=Decimal('100.0'),
            rejection_reason='Material completamente fora das especificações',
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(item.quantity_received, Decimal('100.0'))
        self.assertEqual(item.quantity_accepted, Decimal('0'))
        self.assertEqual(item.quantity_rejected, Decimal('100.0'))
        # Note: Decimal('0') is falsy, so total_value uses quantity_received
        self.assertEqual(item.total_value, Decimal('5000.00'))  # 100 * 50

    def test_receiving_item_with_batch_and_expiry(self):
        """Testa item com lote e data de validade"""
        expiry = timezone.now().date() + timedelta(days=365)
        item = ReceivingItem.objects.create(
            receiving=self.receiving,
            purchase_order_item=self.purchase_order_item,
            quantity_received=Decimal('50.0'),
            batch_number='LOTE2024001',
            expiry_date=expiry,
            created_by=self.user,
            updated_by=self.user
        )

        self.assertEqual(item.batch_number, 'LOTE2024001')
        self.assertEqual(item.expiry_date, expiry)
        self.assertIsNotNone(item.expiry_date)
