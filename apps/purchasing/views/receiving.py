from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
import json

from ..models import (
    PurchaseOrder, PurchaseOrderItem,
    Receiving, ReceivingItem
)
from apps.materials.models import Supplier
from apps.inventory.models import Warehouse, StockMovement


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
