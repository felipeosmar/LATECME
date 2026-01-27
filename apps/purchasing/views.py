from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    PurchaseRequest, PurchaseRequestItem,
    PurchaseOrder, PurchaseOrderItem,
    Receiving, ReceivingItem
)
from apps.materials.models import Material, Supplier
from apps.inventory.models import Warehouse, MaterialStock, StockMovement


@cache_page(300)
@login_required
def dashboard(request):
    """Dashboard de compras"""
    # Estatisticas
    stats = {
        'pending_requests': PurchaseRequest.objects.filter(status='PENDING').count(),
        'approved_requests': PurchaseRequest.objects.filter(status='APPROVED').count(),
        'open_orders': PurchaseOrder.objects.filter(status__in=['SENT', 'CONFIRMED', 'PARTIAL']).count(),
        'pending_receivings': Receiving.objects.filter(status='PENDING').count(),
    }

    # Solicitacoes pendentes de aprovacao
    pending_requests = PurchaseRequest.objects.filter(
        status='PENDING'
    ).select_related('requester', 'warehouse').order_by('-request_date')[:5]

    # Pedidos aguardando recebimento
    pending_orders = PurchaseOrder.objects.filter(
        status__in=['SENT', 'CONFIRMED', 'PARTIAL']
    ).select_related('supplier', 'warehouse').order_by('expected_delivery_date')[:5]

    # Recebimentos pendentes de inspecao
    pending_inspections = Receiving.objects.filter(
        status='PENDING'
    ).select_related('purchase_order', 'received_by').order_by('-receiving_date')[:5]

    context = {
        'stats': stats,
        'pending_requests': pending_requests,
        'pending_orders': pending_orders,
        'pending_inspections': pending_inspections,
    }

    return render(request, 'purchasing/dashboard.html', context)


# =============================================================================
# Purchase Request Views
# =============================================================================

@login_required
def request_list(request):
    """Lista de solicitacoes de compra"""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')

    requests = PurchaseRequest.objects.select_related(
        'requester', 'warehouse', 'approved_by'
    ).prefetch_related('items')

    if search:
        requests = requests.filter(
            Q(reference_number__icontains=search) |
            Q(requester__username__icontains=search) |
            Q(justification__icontains=search)
        )

    if status_filter:
        requests = requests.filter(status=status_filter)

    if priority_filter:
        requests = requests.filter(priority=priority_filter)

    requests = requests.order_by('-request_date', '-created_at')

    # Stats
    stats = {
        'total': PurchaseRequest.objects.count(),
        'draft': PurchaseRequest.objects.filter(status='DRAFT').count(),
        'pending': PurchaseRequest.objects.filter(status='PENDING').count(),
        'approved': PurchaseRequest.objects.filter(status='APPROVED').count(),
    }

    paginator = Paginator(requests, 20)
    page = request.GET.get('page')
    requests = paginator.get_page(page)

    # Dados para filtros
    warehouses = Warehouse.objects.filter(is_active=True)

    context = {
        'requests': requests,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'warehouses': warehouses,
        'status_choices': PurchaseRequest.STATUS_CHOICES,
        'priority_choices': PurchaseRequest.PRIORITY_CHOICES,
    }

    return render(request, 'purchasing/request_list.html', context)


@login_required
def request_detail(request, request_id):
    """Detalhes de uma solicitacao de compra"""
    purchase_request = get_object_or_404(
        PurchaseRequest.objects.select_related('requester', 'warehouse', 'approved_by'),
        id=request_id
    )

    items = purchase_request.items.select_related('material', 'preferred_supplier')

    # Materiais e fornecedores para o formulario
    materials = Material.objects.filter(is_active=True).order_by('code')
    suppliers = Supplier.objects.filter(is_active=True).order_by('trade_name')
    warehouses = Warehouse.objects.filter(is_active=True)

    context = {
        'purchase_request': purchase_request,
        'items': items,
        'materials': materials,
        'suppliers': suppliers,
        'warehouses': warehouses,
        'priority_choices': PurchaseRequest.PRIORITY_CHOICES,
    }

    return render(request, 'purchasing/request_detail.html', context)


@login_required
@require_http_methods(["POST"])
def request_create(request):
    """Criar nova solicitacao de compra"""
    try:
        warehouse_id = request.POST.get('warehouse')
        priority = request.POST.get('priority', 'NORMAL')
        required_date = request.POST.get('required_date') or None
        justification = request.POST.get('justification', '')
        notes = request.POST.get('notes', '')

        if not warehouse_id:
            return JsonResponse({
                'success': False,
                'message': 'Armazem de destino e obrigatorio.'
            })

        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        purchase_request = PurchaseRequest.objects.create(
            requester=request.user,
            warehouse=warehouse,
            priority=priority,
            required_date=required_date,
            justification=justification,
            notes=notes,
            status='DRAFT',
            created_by=request.user,
            updated_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Solicitacao criada com sucesso.',
            'request_id': str(purchase_request.id),
            'redirect_url': f'/purchasing/requests/{purchase_request.id}/'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar solicitacao: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def request_update(request, request_id):
    """Atualizar solicitacao de compra"""
    try:
        purchase_request = get_object_or_404(PurchaseRequest, id=request_id)

        if not purchase_request.can_edit:
            return JsonResponse({
                'success': False,
                'message': 'Esta solicitacao nao pode ser editada.'
            })

        warehouse_id = request.POST.get('warehouse')
        priority = request.POST.get('priority')
        required_date = request.POST.get('required_date') or None
        justification = request.POST.get('justification', '')
        notes = request.POST.get('notes', '')

        if warehouse_id:
            purchase_request.warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        if priority:
            purchase_request.priority = priority
        purchase_request.required_date = required_date
        purchase_request.justification = justification
        purchase_request.notes = notes
        purchase_request.updated_by = request.user
        purchase_request.save()

        return JsonResponse({
            'success': True,
            'message': 'Solicitacao atualizada com sucesso.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao atualizar solicitacao: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def request_submit(request, request_id):
    """Submeter solicitacao para aprovacao"""
    try:
        purchase_request = get_object_or_404(PurchaseRequest, id=request_id)

        if purchase_request.status != 'DRAFT':
            return JsonResponse({
                'success': False,
                'message': 'Apenas solicitacoes em rascunho podem ser submetidas.'
            })

        if not purchase_request.items.exists():
            return JsonResponse({
                'success': False,
                'message': 'Adicione pelo menos um item antes de submeter.'
            })

        purchase_request.status = 'PENDING'
        purchase_request.updated_by = request.user
        purchase_request.save()

        return JsonResponse({
            'success': True,
            'message': 'Solicitacao submetida para aprovacao.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao submeter solicitacao: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def request_approve(request, request_id):
    """Aprovar solicitacao de compra"""
    try:
        purchase_request = get_object_or_404(PurchaseRequest, id=request_id)

        if not purchase_request.can_approve:
            return JsonResponse({
                'success': False,
                'message': 'Esta solicitacao nao pode ser aprovada.'
            })

        purchase_request.status = 'APPROVED'
        purchase_request.approved_by = request.user
        purchase_request.approved_at = timezone.now()
        purchase_request.updated_by = request.user
        purchase_request.save()

        return JsonResponse({
            'success': True,
            'message': 'Solicitacao aprovada com sucesso.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao aprovar solicitacao: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def request_reject(request, request_id):
    """Rejeitar solicitacao de compra"""
    try:
        purchase_request = get_object_or_404(PurchaseRequest, id=request_id)

        if not purchase_request.can_approve:
            return JsonResponse({
                'success': False,
                'message': 'Esta solicitacao nao pode ser rejeitada.'
            })

        data = json.loads(request.body) if request.body else {}
        rejection_reason = data.get('rejection_reason', '')

        purchase_request.status = 'REJECTED'
        purchase_request.approved_by = request.user
        purchase_request.approved_at = timezone.now()
        purchase_request.rejection_reason = rejection_reason
        purchase_request.updated_by = request.user
        purchase_request.save()

        return JsonResponse({
            'success': True,
            'message': 'Solicitacao rejeitada.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao rejeitar solicitacao: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def request_item_add(request, request_id):
    """Adicionar item a solicitacao"""
    try:
        purchase_request = get_object_or_404(PurchaseRequest, id=request_id)

        if not purchase_request.can_edit:
            return JsonResponse({
                'success': False,
                'message': 'Esta solicitacao nao pode ser editada.'
            })

        material_id = request.POST.get('material_id')
        quantity = request.POST.get('quantity')
        estimated_unit_price = request.POST.get('estimated_unit_price') or None
        preferred_supplier_id = request.POST.get('preferred_supplier_id') or None
        notes = request.POST.get('notes', '')

        if not all([material_id, quantity]):
            return JsonResponse({
                'success': False,
                'message': 'Material e quantidade sao obrigatorios.'
            })

        material = get_object_or_404(Material, id=material_id)

        preferred_supplier = None
        if preferred_supplier_id:
            preferred_supplier = get_object_or_404(Supplier, id=preferred_supplier_id)

        item = PurchaseRequestItem.objects.create(
            purchase_request=purchase_request,
            material=material,
            quantity=Decimal(str(quantity)),
            estimated_unit_price=Decimal(str(estimated_unit_price)) if estimated_unit_price else None,
            preferred_supplier=preferred_supplier,
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
def request_item_remove(request, request_id, item_id):
    """Remover item da solicitacao"""
    try:
        purchase_request = get_object_or_404(PurchaseRequest, id=request_id)

        if not purchase_request.can_edit:
            return JsonResponse({
                'success': False,
                'message': 'Esta solicitacao nao pode ser editada.'
            })

        item = get_object_or_404(PurchaseRequestItem, id=item_id, purchase_request=purchase_request)
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


# =============================================================================
# Receiving Views
# =============================================================================

@login_required
def receiving_list(request):
    """Lista de recebimentos"""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    receivings = Receiving.objects.select_related(
        'purchase_order', 'purchase_order__supplier', 'received_by', 'inspected_by'
    ).prefetch_related('items')

    if search:
        receivings = receivings.filter(
            Q(reference_number__icontains=search) |
            Q(purchase_order__reference_number__icontains=search) |
            Q(invoice_number__icontains=search)
        )

    if status_filter:
        receivings = receivings.filter(status=status_filter)

    receivings = receivings.order_by('-receiving_date', '-created_at')

    # Stats
    stats = {
        'total': Receiving.objects.count(),
        'pending': Receiving.objects.filter(status='PENDING').count(),
        'inspecting': Receiving.objects.filter(status='INSPECTING').count(),
        'approved': Receiving.objects.filter(status='APPROVED').count(),
    }

    paginator = Paginator(receivings, 20)
    page = request.GET.get('page')
    receivings = paginator.get_page(page)

    # Pedidos disponiveis para recebimento
    available_orders = PurchaseOrder.objects.filter(
        status__in=['SENT', 'CONFIRMED', 'PARTIAL']
    ).select_related('supplier')

    context = {
        'receivings': receivings,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'available_orders': available_orders,
        'status_choices': Receiving.STATUS_CHOICES,
    }

    return render(request, 'purchasing/receiving_list.html', context)


@login_required
def receiving_detail(request, receiving_id):
    """Detalhes de um recebimento"""
    receiving = get_object_or_404(
        Receiving.objects.select_related(
            'purchase_order', 'purchase_order__supplier',
            'received_by', 'inspected_by'
        ),
        id=receiving_id
    )

    items = receiving.items.select_related('purchase_order_item', 'purchase_order_item__material')

    context = {
        'receiving': receiving,
        'items': items,
    }

    return render(request, 'purchasing/receiving_detail.html', context)


@login_required
def receiving_create(request):
    """Criar novo recebimento"""
    if request.method == 'POST':
        try:
            order_id = request.POST.get('purchase_order')
            invoice_number = request.POST.get('invoice_number', '')
            invoice_date = request.POST.get('invoice_date') or None
            notes = request.POST.get('notes', '')
            items_json = request.POST.get('items', '[]')

            if not order_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Pedido de compra e obrigatorio.'
                })

            order = get_object_or_404(PurchaseOrder, id=order_id)

            if not order.can_receive:
                return JsonResponse({
                    'success': False,
                    'message': 'Este pedido nao pode receber materiais.'
                })

            receiving = Receiving.objects.create(
                purchase_order=order,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                notes=notes,
                received_by=request.user,
                status='PENDING',
                created_by=request.user,
                updated_by=request.user
            )

            # Create receiving items from JSON
            try:
                items = json.loads(items_json)
                for item_data in items:
                    order_item = get_object_or_404(PurchaseOrderItem, id=item_data['order_item_id'])
                    ReceivingItem.objects.create(
                        receiving=receiving,
                        purchase_order_item=order_item,
                        quantity_received=Decimal(str(item_data['received_quantity'])),
                        created_by=request.user,
                        updated_by=request.user
                    )
            except (json.JSONDecodeError, KeyError):
                pass  # No items in request, will be added later

            return JsonResponse({
                'success': True,
                'message': 'Recebimento criado com sucesso.',
                'receiving_id': str(receiving.id),
                'redirect_url': f'/purchasing/receivings/{receiving.id}/'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar recebimento: {str(e)}'
            })
    else:
        # GET - show the form
        confirmed_orders = PurchaseOrder.objects.filter(
            status__in=['SENT', 'CONFIRMED', 'PARTIAL']
        ).select_related('supplier', 'warehouse')

        suppliers = Supplier.objects.filter(is_active=True)
        warehouses = Warehouse.objects.filter(is_active=True)

        # Check if order_id passed via GET param
        selected_order = None
        order_id = request.GET.get('order')
        if order_id:
            try:
                selected_order = PurchaseOrder.objects.get(id=order_id)
            except PurchaseOrder.DoesNotExist:
                pass

        context = {
            'confirmed_orders': confirmed_orders,
            'suppliers': suppliers,
            'warehouses': warehouses,
            'selected_order': selected_order,
        }

        return render(request, 'purchasing/receiving_form.html', context)


@login_required
@require_http_methods(["POST"])
def receiving_item_add(request, receiving_id):
    """Adicionar item ao recebimento"""
    try:
        receiving = get_object_or_404(Receiving, id=receiving_id)

        if receiving.status not in ['PENDING', 'INSPECTING']:
            return JsonResponse({
                'success': False,
                'message': 'Este recebimento nao pode ser editado.'
            })

        order_item_id = request.POST.get('order_item_id')
        quantity_received = request.POST.get('quantity_received')
        batch_number = request.POST.get('batch_number', '')
        expiry_date = request.POST.get('expiry_date') or None
        notes = request.POST.get('notes', '')

        if not all([order_item_id, quantity_received]):
            return JsonResponse({
                'success': False,
                'message': 'Item do pedido e quantidade sao obrigatorios.'
            })

        order_item = get_object_or_404(
            PurchaseOrderItem,
            id=order_item_id,
            purchase_order=receiving.purchase_order
        )

        item = ReceivingItem.objects.create(
            receiving=receiving,
            purchase_order_item=order_item,
            quantity_received=Decimal(str(quantity_received)),
            batch_number=batch_number,
            expiry_date=expiry_date,
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
def receiving_approve(request, receiving_id):
    """Aprovar recebimento e dar entrada no estoque"""
    try:
        receiving = get_object_or_404(Receiving, id=receiving_id)

        if receiving.status not in ['PENDING', 'INSPECTING']:
            return JsonResponse({
                'success': False,
                'message': 'Este recebimento nao pode ser aprovado.'
            })

        if not receiving.items.exists():
            return JsonResponse({
                'success': False,
                'message': 'Adicione pelo menos um item antes de aprovar.'
            })

        # Processar itens
        for item in receiving.items.all():
            # Definir quantidade aceita = quantidade recebida se nao especificada
            if item.quantity_accepted is None:
                item.quantity_accepted = item.quantity_received
                item.save()

            # Atualizar quantidade recebida no item do pedido
            order_item = item.purchase_order_item
            order_item.received_quantity += item.quantity_accepted
            order_item.save()

            # Criar movimentacao de entrada no estoque
            StockMovement.objects.create(
                material=order_item.material,
                warehouse=receiving.purchase_order.warehouse,
                movement_type='IN',
                reason='PURCHASE',
                quantity=item.quantity_accepted,
                unit_cost=order_item.unit_price,
                reference_document=receiving.reference_number,
                batch_number=item.batch_number,
                notes=f'Recebimento {receiving.reference_number} - NF {receiving.invoice_number}',
                user=request.user,
                created_by=request.user,
                updated_by=request.user
            )

        # Atualizar status do recebimento
        receiving.status = 'APPROVED'
        receiving.inspected_by = request.user
        receiving.inspection_date = timezone.now()
        receiving.updated_by = request.user
        receiving.save()

        # Verificar se pedido foi completamente recebido
        order = receiving.purchase_order
        all_received = all(item.is_fully_received for item in order.items.all())
        if all_received:
            order.status = 'RECEIVED'
        else:
            order.status = 'PARTIAL'
        order.updated_by = request.user
        order.save()

        return JsonResponse({
            'success': True,
            'message': 'Recebimento aprovado e estoque atualizado.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao aprovar recebimento: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def receiving_reject(request, receiving_id):
    """Rejeitar recebimento"""
    try:
        receiving = get_object_or_404(Receiving, id=receiving_id)

        if receiving.status not in ['PENDING', 'INSPECTING']:
            return JsonResponse({
                'success': False,
                'message': 'Este recebimento nao pode ser rejeitado.'
            })

        data = json.loads(request.body) if request.body else {}
        rejection_reason = data.get('rejection_reason', '')

        receiving.status = 'REJECTED'
        receiving.inspected_by = request.user
        receiving.inspection_date = timezone.now()
        receiving.rejection_reason = rejection_reason
        receiving.updated_by = request.user
        receiving.save()

        return JsonResponse({
            'success': True,
            'message': 'Recebimento rejeitado.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao rejeitar recebimento: {str(e)}'
        })


# =============================================================================
# API Endpoints
# =============================================================================

@login_required
def api_approved_requests(request):
    """API: Lista solicitacoes aprovadas disponiveis para criar pedido"""
    requests = PurchaseRequest.objects.filter(
        status='APPROVED'
    ).select_related('requester', 'warehouse').order_by('-request_date')

    data = [
        {
            'id': str(r.id),
            'reference_number': r.reference_number,
            'requester': r.requester.get_full_name() or r.requester.username,
            'warehouse': r.warehouse.code,
            'total_value': float(r.total_value),
            'items_count': r.items.count()
        }
        for r in requests
    ]
    return JsonResponse(data, safe=False)


@login_required
def api_order_items(request, order_id):
    """API: Lista itens pendentes de um pedido para recebimento"""
    order = get_object_or_404(PurchaseOrder, id=order_id)

    items = order.items.select_related('material')

    data = [
        {
            'id': str(item.id),
            'material_id': str(item.material.id),
            'material_code': item.material.code,
            'material_name': item.material.name,
            'unit': item.material.unit_of_measure,
            'quantity': float(item.quantity),
            'received': float(item.received_quantity),
            'pending': float(item.pending_quantity),
            'unit_price': float(item.unit_price)
        }
        for item in items
    ]
    return JsonResponse({'success': True, 'items': data})
