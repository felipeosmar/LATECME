from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..models import (
    Warehouse, MaterialStock, StockMovement,
    InventoryCount, InventoryCountItem
)
from apps.accounts.models import CustomUser
from decimal import Decimal


@login_required
def inventory_count_list(request):
    """Lista de contagens de inventário"""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    warehouse_id = request.GET.get('warehouse', '')

    counts = InventoryCount.objects.select_related(
        'warehouse', 'counter', 'supervisor'
    ).prefetch_related('items')

    if search:
        counts = counts.filter(
            Q(reference_number__icontains=search) |
            Q(warehouse__code__icontains=search) |
            Q(warehouse__name__icontains=search)
        )

    if status_filter:
        counts = counts.filter(status=status_filter)

    if warehouse_id:
        counts = counts.filter(warehouse_id=warehouse_id)

    counts = counts.order_by('-count_date', '-created_at')

    # Estatísticas
    stats = {
        'total': InventoryCount.objects.count(),
        'planned': InventoryCount.objects.filter(status='PLANNED').count(),
        'in_progress': InventoryCount.objects.filter(status='IN_PROGRESS').count(),
        'completed': InventoryCount.objects.filter(status='COMPLETED').count(),
    }

    paginator = Paginator(counts, 20)
    page = request.GET.get('page')
    counts = paginator.get_page(page)

    # Dados para filtros
    warehouses = Warehouse.objects.filter(is_active=True)
    users = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')

    context = {
        'counts': counts,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'warehouses': warehouses,
        'users': users,
        'selected_warehouse': warehouse_id,
        'status_choices': InventoryCount.STATUS_CHOICES,
    }

    return render(request, 'inventory/inventory_count_list.html', context)


@login_required
def inventory_count_detail(request, count_id):
    """Detalhes de uma contagem de inventário"""
    count = get_object_or_404(
        InventoryCount.objects.select_related('warehouse', 'counter', 'supervisor'),
        id=count_id
    )

    items = count.items.select_related('material').order_by('material__code')

    # Calcular estatísticas
    total_items = items.count()
    counted_items = items.filter(counted_quantity__isnull=False).count()
    items_with_variance = 0
    total_variance = Decimal('0')

    for item in items:
        if item.variance is not None and item.variance != 0:
            items_with_variance += 1
            total_variance += abs(item.variance)

    context = {
        'count': count,
        'items': items,
        'total_items': total_items,
        'counted_items': counted_items,
        'items_with_variance': items_with_variance,
        'total_variance': total_variance,
    }

    return render(request, 'inventory/inventory_count_detail.html', context)


@login_required
@require_http_methods(["POST"])
def inventory_count_create(request):
    """Criar nova contagem de inventário"""
    try:
        warehouse_id = request.POST.get('warehouse')
        count_date = request.POST.get('count_date')
        counter_id = request.POST.get('counter')
        supervisor_id = request.POST.get('supervisor')
        notes = request.POST.get('notes', '')

        if not all([warehouse_id, count_date]):
            return JsonResponse({
                'success': False,
                'message': 'Armazém e data da contagem são obrigatórios.'
            })

        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        counter = None
        if counter_id:
            counter = get_object_or_404(CustomUser, id=counter_id)

        supervisor = None
        if supervisor_id:
            supervisor = get_object_or_404(CustomUser, id=supervisor_id)

        if counter and supervisor and counter == supervisor:
            return JsonResponse({
                'success': False,
                'message': 'O contador e o supervisor devem ser pessoas diferentes.'
            })

        count = InventoryCount.objects.create(
            warehouse=warehouse,
            count_date=count_date,
            counter=counter,
            supervisor=supervisor,
            notes=notes,
            status='PLANNED',
            created_by=request.user,
            updated_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Contagem criada com sucesso.',
            'count_id': str(count.id),
            'redirect_url': f'/inventory/counts/{count.id}/'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar contagem: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def inventory_count_start(request, count_id):
    """Iniciar contagem - muda status e popula itens do estoque"""
    try:
        count = get_object_or_404(InventoryCount, id=count_id)

        if count.status != 'PLANNED':
            return JsonResponse({
                'success': False,
                'message': 'Apenas contagens planejadas podem ser iniciadas.'
            })

        # Obter todos os materiais em estoque no armazém
        stocks = MaterialStock.objects.filter(
            warehouse=count.warehouse,
            current_quantity__gt=0
        ).select_related('material')

        if not stocks.exists():
            return JsonResponse({
                'success': False,
                'message': 'Não há materiais em estoque neste armazém.'
            })

        # Criar itens da contagem
        items_created = 0
        for stock in stocks:
            InventoryCountItem.objects.create(
                inventory_count=count,
                material=stock.material,
                system_quantity=stock.current_quantity,
                location_code=stock.location_code or '',
                created_by=request.user,
                updated_by=request.user
            )
            items_created += 1

        # Atualizar status
        count.status = 'IN_PROGRESS'
        count.updated_by = request.user
        count.save()

        return JsonResponse({
            'success': True,
            'message': f'Contagem iniciada com {items_created} itens.',
            'items_created': items_created
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao iniciar contagem: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def inventory_count_save_items(request, count_id):
    """Salvar quantidades contadas"""
    import json

    try:
        count = get_object_or_404(InventoryCount, id=count_id)

        if count.status != 'IN_PROGRESS':
            return JsonResponse({
                'success': False,
                'message': 'Apenas contagens em andamento podem ser editadas.'
            })

        data = json.loads(request.body)
        items_data = data.get('items', [])

        updated_count = 0
        for item_data in items_data:
            item_id = item_data.get('id')
            counted_quantity = item_data.get('counted_quantity')
            notes = item_data.get('notes', '')

            if item_id:
                try:
                    item = InventoryCountItem.objects.get(
                        id=item_id,
                        inventory_count=count
                    )
                    if counted_quantity is not None and counted_quantity != '':
                        item.counted_quantity = Decimal(str(counted_quantity))
                    item.notes = notes
                    item.updated_by = request.user
                    item.save()
                    updated_count += 1
                except InventoryCountItem.DoesNotExist:
                    pass

        return JsonResponse({
            'success': True,
            'message': f'{updated_count} itens atualizados.',
            'updated_count': updated_count
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dados inválidos.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao salvar itens: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def inventory_count_complete(request, count_id):
    """Completar contagem"""
    try:
        count = get_object_or_404(InventoryCount, id=count_id)

        if count.status != 'IN_PROGRESS':
            return JsonResponse({
                'success': False,
                'message': 'Apenas contagens em andamento podem ser completadas.'
            })

        # Verificar se todos os itens foram contados
        uncounted_items = count.items.filter(counted_quantity__isnull=True).count()
        if uncounted_items > 0:
            return JsonResponse({
                'success': False,
                'message': f'Ainda há {uncounted_items} itens não contados.'
            })

        count.status = 'COMPLETED'
        count.updated_by = request.user
        count.save()

        return JsonResponse({
            'success': True,
            'message': 'Contagem completada com sucesso.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao completar contagem: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def inventory_count_cancel(request, count_id):
    """Cancelar contagem"""
    try:
        count = get_object_or_404(InventoryCount, id=count_id)

        if count.status == 'COMPLETED':
            return JsonResponse({
                'success': False,
                'message': 'Contagens completadas não podem ser canceladas.'
            })

        count.status = 'CANCELLED'
        count.updated_by = request.user
        count.save()

        return JsonResponse({
            'success': True,
            'message': 'Contagem cancelada.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao cancelar contagem: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def inventory_count_generate_adjustments(request, count_id):
    """Gerar movimentações de ajuste baseadas nas variações"""
    try:
        count = get_object_or_404(InventoryCount, id=count_id)

        if count.status != 'COMPLETED':
            return JsonResponse({
                'success': False,
                'message': 'Apenas contagens completadas podem gerar ajustes.'
            })

        items_with_variance = count.items.filter(
            counted_quantity__isnull=False
        ).exclude(
            counted_quantity=F('system_quantity')
        )

        adjustments_created = 0
        for item in items_with_variance:
            variance = item.counted_quantity - item.system_quantity

            if variance != 0:
                # Criar movimentação de ajuste
                movement_type = 'ADJUSTMENT'
                StockMovement.objects.create(
                    material=item.material,
                    warehouse=count.warehouse,
                    movement_type=movement_type,
                    reason='INVENTORY_ADJUSTMENT',
                    quantity=item.counted_quantity,  # Ajuste define a quantidade final
                    reference_document=count.reference_number,
                    notes=f'Ajuste de inventário - Contagem {count.reference_number}. '
                          f'Sistema: {item.system_quantity} kg, Contado: {item.counted_quantity} kg, '
                          f'Variação: {variance} kg',
                    user=request.user,
                    created_by=request.user,
                    updated_by=request.user
                )
                adjustments_created += 1

        return JsonResponse({
            'success': True,
            'message': f'{adjustments_created} ajustes de estoque criados.',
            'adjustments_created': adjustments_created
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao gerar ajustes: {str(e)}'
        })
