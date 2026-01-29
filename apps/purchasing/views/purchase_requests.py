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
