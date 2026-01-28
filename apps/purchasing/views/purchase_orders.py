from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
import json

from ..models import (
    PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    Receiving, ReceivingItem
)
from apps.materials.models import Material, Supplier
from apps.inventory.models import Warehouse, MaterialStock, StockMovement


# =============================================================================
# Purchase Order Views
# =============================================================================

@login_required
def order_list(request):
    """Lista de pedidos de compra"""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    supplier_id = request.GET.get('supplier', '')

    orders = PurchaseOrder.objects.select_related(
        'supplier', 'warehouse', 'buyer'
    ).prefetch_related('items')

    if search:
        orders = orders.filter(
            Q(reference_number__icontains=search) |
            Q(supplier__trade_name__icontains=search) |
            Q(supplier__legal_name__icontains=search)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    if supplier_id:
        orders = orders.filter(supplier_id=supplier_id)

    orders = orders.order_by('-order_date', '-created_at')

    # Stats
    stats = {
        'total': PurchaseOrder.objects.count(),
        'draft': PurchaseOrder.objects.filter(status='DRAFT').count(),
        'sent': PurchaseOrder.objects.filter(status='SENT').count(),
        'partial': PurchaseOrder.objects.filter(status='PARTIAL').count(),
    }

    paginator = Paginator(orders, 20)
    page = request.GET.get('page')
    orders = paginator.get_page(page)

    # Dados para filtros
    suppliers = Supplier.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)

    context = {
        'orders': orders,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'supplier_id': supplier_id,
        'suppliers': suppliers,
        'warehouses': warehouses,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
    }

    return render(request, 'purchasing/order_list.html', context)


@login_required
def order_detail(request, order_id):
    """Detalhes de um pedido de compra"""
    order = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier', 'warehouse', 'buyer', 'purchase_request'),
        id=order_id
    )

    items = order.items.select_related('material')
    receivings = order.receivings.select_related('received_by').order_by('-receiving_date')

    # Dados para formularios
    materials = Material.objects.filter(is_active=True).order_by('code')

    context = {
        'order': order,
        'items': items,
        'receivings': receivings,
        'materials': materials,
    }

    return render(request, 'purchasing/order_detail.html', context)


@login_required
@require_http_methods(["POST"])
def order_create(request):
    """Criar novo pedido de compra"""
    try:
        supplier_id = request.POST.get('supplier')
        warehouse_id = request.POST.get('warehouse')
        purchase_request_id = request.POST.get('purchase_request') or None
        expected_delivery_date = request.POST.get('expected_delivery_date') or None
        payment_terms = request.POST.get('payment_terms', '')
        notes = request.POST.get('notes', '')

        if not all([supplier_id, warehouse_id]):
            return JsonResponse({
                'success': False,
                'message': 'Fornecedor e armazem sao obrigatorios.'
            })

        supplier = get_object_or_404(Supplier, id=supplier_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        purchase_request = None
        if purchase_request_id:
            purchase_request = get_object_or_404(PurchaseRequest, id=purchase_request_id)

        order = PurchaseOrder.objects.create(
            supplier=supplier,
            warehouse=warehouse,
            purchase_request=purchase_request,
            expected_delivery_date=expected_delivery_date,
            payment_terms=payment_terms,
            notes=notes,
            buyer=request.user,
            status='DRAFT',
            created_by=request.user,
            updated_by=request.user
        )

        # Se criado a partir de uma solicitacao, copiar itens
        if purchase_request:
            for req_item in purchase_request.items.all():
                PurchaseOrderItem.objects.create(
                    purchase_order=order,
                    material=req_item.material,
                    quantity=req_item.quantity,
                    unit_price=req_item.estimated_unit_price or Decimal('0'),
                    created_by=request.user,
                    updated_by=request.user
                )
            # Atualizar status da solicitacao
            purchase_request.status = 'ORDERED'
            purchase_request.updated_by = request.user
            purchase_request.save()

        return JsonResponse({
            'success': True,
            'message': 'Pedido criado com sucesso.',
            'order_id': str(order.id),
            'redirect_url': f'/purchasing/orders/{order.id}/'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar pedido: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def order_send(request, order_id):
    """Marcar pedido como enviado ao fornecedor"""
    try:
        order = get_object_or_404(PurchaseOrder, id=order_id)

        if order.status != 'DRAFT':
            return JsonResponse({
                'success': False,
                'message': 'Apenas pedidos em rascunho podem ser enviados.'
            })

        if not order.items.exists():
            return JsonResponse({
                'success': False,
                'message': 'Adicione pelo menos um item antes de enviar.'
            })

        order.status = 'SENT'
        order.updated_by = request.user
        order.save()

        return JsonResponse({
            'success': True,
            'message': 'Pedido marcado como enviado.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao enviar pedido: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def order_confirm(request, order_id):
    """Confirmar pedido (fornecedor confirmou)"""
    try:
        order = get_object_or_404(PurchaseOrder, id=order_id)

        if order.status != 'SENT':
            return JsonResponse({
                'success': False,
                'message': 'Apenas pedidos enviados podem ser confirmados.'
            })

        order.status = 'CONFIRMED'
        order.updated_by = request.user
        order.save()

        return JsonResponse({
            'success': True,
            'message': 'Pedido confirmado.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao confirmar pedido: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def order_item_add(request, order_id):
    """Adicionar item ao pedido"""
    try:
        order = get_object_or_404(PurchaseOrder, id=order_id)

        if order.status != 'DRAFT':
            return JsonResponse({
                'success': False,
                'message': 'Apenas pedidos em rascunho podem ser editados.'
            })

        material_id = request.POST.get('material_id')
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        notes = request.POST.get('notes', '')

        if not all([material_id, quantity, unit_price]):
            return JsonResponse({
                'success': False,
                'message': 'Material, quantidade e preco unitario sao obrigatorios.'
            })

        material = get_object_or_404(Material, id=material_id)

        item = PurchaseOrderItem.objects.create(
            purchase_order=order,
            material=material,
            quantity=Decimal(str(quantity)),
            unit_price=Decimal(str(unit_price)),
            notes=notes,
            created_by=request.user,
            updated_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Item adicionado com sucesso.',
            'item_id': str(item.id)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao adicionar item: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def order_item_remove(request, order_id, item_id):
    """Remover item do pedido"""
    try:
        order = get_object_or_404(PurchaseOrder, id=order_id)

        if order.status != 'DRAFT':
            return JsonResponse({
                'success': False,
                'message': 'Apenas pedidos em rascunho podem ser editados.'
            })

        item = get_object_or_404(PurchaseOrderItem, id=item_id, purchase_order=order)
        item.delete()

        return JsonResponse({
            'success': True,
            'message': 'Item removido com sucesso.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao remover item: {str(e)}'
        })
