from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import (
    Warehouse, MaterialStock, StockMovement,
    StockReservation, InventoryCount, InventoryCountItem
)
from apps.materials.models import Material
from apps.accounts.models import CustomUser
from datetime import datetime, timedelta
from decimal import Decimal


@login_required
def dashboard(request):
    """Dashboard principal do inventário"""
    # Estatísticas gerais
    total_warehouses = Warehouse.objects.filter(is_active=True).count()
    total_materials = MaterialStock.objects.values('material').distinct().count()
    total_stock_value = MaterialStock.objects.aggregate(
        total=Sum(F('current_quantity') * F('material__materialsupplier__price_per_kg'))
    )['total'] or 0

    # Materiais com estoque baixo
    low_stock_items = MaterialStock.objects.filter(
        current_quantity__lte=F('minimum_stock'),
        current_quantity__gt=0
    ).select_related('material', 'warehouse')[:10]

    # Materiais sem estoque
    out_of_stock_items = MaterialStock.objects.filter(
        current_quantity=0
    ).select_related('material', 'warehouse')[:10]

    # Movimentações recentes
    recent_movements = StockMovement.objects.select_related(
        'material', 'warehouse', 'user'
    ).order_by('-created_at')[:10]

    # Reservas ativas
    active_reservations = StockReservation.objects.filter(
        expiry_date__gt=timezone.now()
    ).select_related('material', 'warehouse', 'reserved_by')[:10]

    context = {
        'total_warehouses': total_warehouses,
        'total_materials': total_materials,
        'total_stock_value': total_stock_value,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'recent_movements': recent_movements,
        'active_reservations': active_reservations,
    }

    return render(request, 'inventory/dashboard.html', context)


@login_required
def stock_list(request):
    """Lista de estoques"""
    # Filtros
    search = request.GET.get('search', '')
    warehouse_id = request.GET.get('warehouse', '')
    material_type = request.GET.get('material_type', '')
    stock_status = request.GET.get('stock_status', '')

    # Query base
    stocks = MaterialStock.objects.select_related(
        'material', 'warehouse'
    ).prefetch_related('material__materialsupplier_set')

    # Aplicar filtros
    if search:
        stocks = stocks.filter(
            Q(material__code__icontains=search) |
            Q(material__name__icontains=search) |
            Q(warehouse__code__icontains=search) |
            Q(warehouse__name__icontains=search)
        )

    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)

    if material_type:
        stocks = stocks.filter(material__material_type=material_type)

    if stock_status == 'low':
        stocks = stocks.filter(current_quantity__lte=F('minimum_stock'))
    elif stock_status == 'out':
        stocks = stocks.filter(current_quantity=0)
    elif stock_status == 'normal':
        stocks = stocks.filter(current_quantity__gt=F('minimum_stock'))

    # Ordenação
    stocks = stocks.order_by('material__code', 'warehouse__code')

    # Paginação
    paginator = Paginator(stocks, 25)
    page = request.GET.get('page')
    stocks = paginator.get_page(page)

    # Dados para filtros
    warehouses = Warehouse.objects.filter(is_active=True)
    material_types = Material.MATERIAL_TYPES

    context = {
        'stocks': stocks,
        'search': search,
        'warehouses': warehouses,
        'material_types': material_types,
        'selected_warehouse': warehouse_id,
        'selected_material_type': material_type,
        'selected_stock_status': stock_status,
    }

    return render(request, 'inventory/stock_list.html', context)


@login_required
def stock_detail(request, stock_id):
    """Detalhes de um estoque específico"""
    stock = get_object_or_404(MaterialStock, id=stock_id)

    # Histórico de movimentações
    movements = StockMovement.objects.filter(
        material=stock.material,
        warehouse=stock.warehouse
    ).select_related('user').order_by('-created_at')[:20]

    # Reservas ativas
    reservations = StockReservation.objects.filter(
        material=stock.material,
        warehouse=stock.warehouse,
        expiry_date__gt=timezone.now()
    ).select_related('reserved_by')

    context = {
        'stock': stock,
        'movements': movements,
        'reservations': reservations,
    }

    return render(request, 'inventory/stock_detail.html', context)


@login_required
def movements_list(request):
    """Lista de movimentações"""
    # Filtros
    search = request.GET.get('search', '')
    movement_type = request.GET.get('movement_type', '')
    warehouse_id = request.GET.get('warehouse', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Query base
    movements = StockMovement.objects.select_related(
        'material', 'warehouse', 'user', 'destination_warehouse'
    )

    # Aplicar filtros
    if search:
        movements = movements.filter(
            Q(material__code__icontains=search) |
            Q(material__name__icontains=search) |
            Q(reference_document__icontains=search) |
            Q(batch_number__icontains=search)
        )

    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    if warehouse_id:
        movements = movements.filter(warehouse_id=warehouse_id)

    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            movements = movements.filter(created_at__date__gte=date_from)
        except ValueError:
            pass

    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            movements = movements.filter(created_at__date__lte=date_to)
        except ValueError:
            pass

    # Ordenação
    movements = movements.order_by('-created_at')

    # Paginação
    paginator = Paginator(movements, 25)
    page = request.GET.get('page')
    movements = paginator.get_page(page)

    # Dados para filtros e formulário
    warehouses = Warehouse.objects.filter(is_active=True)
    materials = Material.objects.filter(is_active=True).order_by('code')
    movement_types = StockMovement.MOVEMENT_TYPES

    context = {
        'movements': movements,
        'search': search,
        'warehouses': warehouses,
        'materials': materials,
        'movement_types': movement_types,
        'selected_movement_type': movement_type,
        'selected_warehouse': warehouse_id,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'inventory/movements_list.html', context)


@login_required
def warehouse_list(request):
    """Lista de armazéns"""
    search = request.GET.get('search', '')

    warehouses = Warehouse.objects.all()

    if search:
        warehouses = warehouses.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(location__icontains=search)
        )

    # Adicionar estatísticas
    warehouses = warehouses.annotate(
        total_materials=Count('materialstock__material', distinct=True),
        total_stock_quantity=Sum('materialstock__current_quantity')
    ).order_by('code')

    paginator = Paginator(warehouses, 20)
    page = request.GET.get('page')
    warehouses = paginator.get_page(page)

    context = {
        'warehouses': warehouses,
        'search': search,
    }

    return render(request, 'inventory/warehouse_list.html', context)


@login_required
def warehouse_detail(request, warehouse_id):
    """Detalhes de um armazém"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)

    # Se for uma requisição AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'id': str(warehouse.id),
            'code': warehouse.code,
            'name': warehouse.name,
            'location': warehouse.location,
            'manager_id': str(warehouse.manager.id) if warehouse.manager else None,
            'description': warehouse.description or '',
            'is_active': warehouse.is_active
        })

    # Estoques do armazém
    stocks = MaterialStock.objects.filter(
        warehouse=warehouse
    ).select_related('material').order_by('material__code')

    # Estatísticas
    total_materials = stocks.count()
    total_quantity = stocks.aggregate(Sum('current_quantity'))['current_quantity__sum'] or 0
    low_stock_count = stocks.filter(current_quantity__lte=F('minimum_stock')).count()
    out_of_stock_count = stocks.filter(current_quantity=0).count()

    # Movimentações recentes
    recent_movements = StockMovement.objects.filter(
        warehouse=warehouse
    ).select_related('material', 'user').order_by('-created_at')[:10]

    context = {
        'warehouse': warehouse,
        'stocks': stocks,
        'total_materials': total_materials,
        'total_quantity': total_quantity,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'recent_movements': recent_movements,
    }

    return render(request, 'inventory/warehouse_detail.html', context)


@login_required
def reservations_list(request):
    """Lista de reservas"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'active')

    reservations = StockReservation.objects.select_related(
        'material', 'warehouse', 'reserved_by'
    )

    if search:
        reservations = reservations.filter(
            Q(material__code__icontains=search) |
            Q(material__name__icontains=search) |
            Q(purpose__icontains=search)
        )

    if status == 'active':
        reservations = reservations.filter(expiry_date__gt=timezone.now())
    elif status == 'expired':
        reservations = reservations.filter(expiry_date__lte=timezone.now())

    reservations = reservations.order_by('-reservation_date')

    paginator = Paginator(reservations, 20)
    page = request.GET.get('page')
    reservations = paginator.get_page(page)

    context = {
        'reservations': reservations,
        'search': search,
        'status': status,
    }

    return render(request, 'inventory/reservations_list.html', context)


@login_required
@require_http_methods(["POST"])
def create_movement(request):
    """Criar nova movimentação via AJAX"""
    try:
        material_id = request.POST.get('material_id')
        warehouse_id = request.POST.get('warehouse_id')
        movement_type = request.POST.get('movement_type')
        reason = request.POST.get('reason')
        quantity = Decimal(request.POST.get('quantity', '0'))
        unit_cost = request.POST.get('unit_cost')
        reference_document = request.POST.get('reference_document', '')
        notes = request.POST.get('notes', '')

        # Validações
        if not all([material_id, warehouse_id, movement_type, reason, quantity]):
            return JsonResponse({
                'success': False,
                'message': 'Todos os campos obrigatórios devem ser preenchidos.'
            })

        if quantity <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Quantidade deve ser maior que zero.'
            })

        # Obter objetos
        material = get_object_or_404(Material, id=material_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        # Verificar se há estoque suficiente para saídas
        if movement_type == 'OUT':
            try:
                stock = MaterialStock.objects.get(
                    material=material,
                    warehouse=warehouse
                )
                if stock.available_quantity < quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'Estoque insuficiente. Disponível: {stock.available_quantity} kg'
                    })
            except MaterialStock.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Material não encontrado no estoque.'
                })

        # Criar movimentação
        movement = StockMovement.objects.create(
            material=material,
            warehouse=warehouse,
            movement_type=movement_type,
            reason=reason,
            quantity=quantity,
            unit_cost=Decimal(unit_cost) if unit_cost else None,
            reference_document=reference_document,
            notes=notes,
            user=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Movimentação criada com sucesso.',
            'movement_id': movement.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar movimentação: {str(e)}'
        })


@login_required
def reports(request):
    """Relatórios de inventário"""
    # Período
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()

    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

    # Movimentações por tipo
    movements_by_type = StockMovement.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).values('movement_type').annotate(
        count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('movement_type')

    # Materiais mais movimentados
    top_materials = StockMovement.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).values('material__code', 'material__name').annotate(
        total_movements=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-total_movements')[:10]

    # Armazéns mais ativos
    top_warehouses = StockMovement.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).values('warehouse__code', 'warehouse__name').annotate(
        total_movements=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-total_movements')[:10]

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'movements_by_type': movements_by_type,
        'top_materials': top_materials,
        'top_warehouses': top_warehouses,
    }

    return render(request, 'inventory/reports.html', context)


@login_required
@require_http_methods(["POST"])
def warehouse_create(request):
    """Criar novo armazém via AJAX"""
    try:
        code = request.POST.get('code', '').strip()
        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        manager_id = request.POST.get('manager_id', '')
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        # Validações
        if not all([code, name, location]):
            return JsonResponse({
                'success': False,
                'message': 'Código, nome e localização são obrigatórios.'
            })

        # Verificar se código já existe
        if Warehouse.objects.filter(code=code).exists():
            return JsonResponse({
                'success': False,
                'message': f'Já existe um armazém com o código {code}.'
            })

        # Obter manager se fornecido
        manager = None
        if manager_id:
            try:
                manager = CustomUser.objects.get(id=manager_id)
            except CustomUser.DoesNotExist:
                pass

        # Criar armazém
        warehouse = Warehouse.objects.create(
            code=code,
            name=name,
            location=location,
            manager=manager,
            description=description,
            is_active=is_active,
            created_by=request.user,
            updated_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Armazém criado com sucesso.',
            'warehouse_id': str(warehouse.id)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar armazém: {str(e)}'
        })


@login_required
@require_http_methods(["PUT"])
def warehouse_update(request, warehouse_id):
    """Atualizar armazém via AJAX"""
    try:
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        # Parse PUT data
        put_data = request.body.decode('utf-8')
        data = {}
        for param in put_data.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                data[key] = value

        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        location = data.get('location', '').strip()
        manager_id = data.get('manager_id', '')
        description = data.get('description', '').strip()
        is_active = data.get('is_active') == 'on'

        # Validações
        if not all([code, name, location]):
            return JsonResponse({
                'success': False,
                'message': 'Código, nome e localização são obrigatórios.'
            })

        # Verificar se código já existe (exceto para o próprio armazém)
        if Warehouse.objects.filter(code=code).exclude(id=warehouse_id).exists():
            return JsonResponse({
                'success': False,
                'message': f'Já existe outro armazém com o código {code}.'
            })

        # Obter manager se fornecido
        manager = None
        if manager_id:
            try:
                manager = CustomUser.objects.get(id=manager_id)
            except CustomUser.DoesNotExist:
                pass

        # Atualizar armazém
        warehouse.code = code
        warehouse.name = name
        warehouse.location = location
        warehouse.manager = manager
        warehouse.description = description
        warehouse.is_active = is_active
        warehouse.updated_by = request.user
        warehouse.save()

        return JsonResponse({
            'success': True,
            'message': 'Armazém atualizado com sucesso.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao atualizar armazém: {str(e)}'
        })


# =============================================================================
# Inventory Count Views
# =============================================================================

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


# =============================================================================
# API Endpoints for Reservations and Stock
# =============================================================================

@login_required
def api_materials_with_stock(request):
    """API: Lista materiais que possuem estoque"""
    materials = Material.objects.filter(
        is_active=True,
        materialstock__current_quantity__gt=0
    ).distinct().order_by('code')

    data = [
        {
            'id': str(m.id),
            'code': m.code,
            'name': m.name,
            'material_type': m.material_type
        }
        for m in materials
    ]
    return JsonResponse(data, safe=False)


@login_required
def api_warehouses(request):
    """API: Lista armazéns ativos"""
    warehouses = Warehouse.objects.filter(is_active=True).order_by('code')

    data = [
        {
            'id': str(w.id),
            'code': w.code,
            'name': w.name,
            'location': w.location or ''
        }
        for w in warehouses
    ]
    return JsonResponse(data, safe=False)


@login_required
def api_stock_info(request, material_id, warehouse_id):
    """API: Informações de estoque de um material em um armazém"""
    try:
        stock = MaterialStock.objects.get(
            material_id=material_id,
            warehouse_id=warehouse_id
        )
        data = {
            'current_quantity': float(stock.current_quantity),
            'reserved_quantity': float(stock.reserved_quantity),
            'available_quantity': float(stock.available_quantity),
            'minimum_stock': float(stock.minimum_stock) if stock.minimum_stock else None,
            'location_code': stock.location_code or ''
        }
        return JsonResponse(data)
    except MaterialStock.DoesNotExist:
        return JsonResponse({
            'current_quantity': 0,
            'reserved_quantity': 0,
            'available_quantity': 0,
            'minimum_stock': None,
            'location_code': ''
        })


@login_required
def reservation_detail(request, reservation_id):
    """API: Detalhes de uma reserva"""
    reservation = get_object_or_404(StockReservation, id=reservation_id)

    data = {
        'id': str(reservation.id),
        'material_id': str(reservation.material_id),
        'material_code': reservation.material.code,
        'material_name': reservation.material.name,
        'warehouse_id': str(reservation.warehouse_id),
        'warehouse_code': reservation.warehouse.code,
        'warehouse_name': reservation.warehouse.name,
        'quantity': float(reservation.quantity),
        'purpose': reservation.purpose,
        'reference_document': reservation.reference_document or '',
        'notes': reservation.notes or '',
        'reservation_date': reservation.reservation_date.strftime('%d/%m/%Y %H:%M') if reservation.reservation_date else '',
        'expiry_date': reservation.expiry_date.strftime('%d/%m/%Y %H:%M') if reservation.expiry_date else '',
        'expiry_date_iso': reservation.expiry_date.strftime('%Y-%m-%dT%H:%M') if reservation.expiry_date else '',
        'is_expired': reservation.is_expired,
        'reserved_by_name': reservation.reserved_by.get_full_name() if reservation.reserved_by else '',
        'reserved_by_email': reservation.reserved_by.email if reservation.reserved_by else '',
        'created_at': reservation.created_at.strftime('%d/%m/%Y %H:%M') if reservation.created_at else '',
        'created_by_name': reservation.created_by.get_full_name() if reservation.created_by else ''
    }
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def reservation_create(request):
    """API: Criar nova reserva"""
    import json

    try:
        data = json.loads(request.body)

        material_id = data.get('material_id')
        warehouse_id = data.get('warehouse_id')
        quantity = data.get('quantity')
        expiry_date = data.get('expiry_date')
        purpose = data.get('purpose', '')
        reference_document = data.get('reference_document', '')
        notes = data.get('notes', '')

        if not all([material_id, warehouse_id, quantity, expiry_date, purpose]):
            return JsonResponse({
                'success': False,
                'message': 'Material, armazém, quantidade, data de expiração e finalidade são obrigatórios.'
            })

        material = get_object_or_404(Material, id=material_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        # Verificar estoque disponível
        try:
            stock = MaterialStock.objects.get(material=material, warehouse=warehouse)
            if not stock.can_reserve(Decimal(str(quantity))):
                return JsonResponse({
                    'success': False,
                    'message': f'Estoque insuficiente. Disponível: {stock.available_quantity} kg'
                })
        except MaterialStock.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Material não encontrado no estoque deste armazém.'
            })

        # Criar reserva
        reservation = StockReservation.objects.create(
            material=material,
            warehouse=warehouse,
            quantity=Decimal(str(quantity)),
            expiry_date=expiry_date,
            purpose=purpose,
            reference_document=reference_document,
            notes=notes,
            reserved_by=request.user,
            created_by=request.user,
            updated_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Reserva criada com sucesso.',
            'reservation_id': str(reservation.id)
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dados inválidos.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar reserva: {str(e)}'
        })


@login_required
@require_http_methods(["PUT"])
def reservation_update(request, reservation_id):
    """API: Atualizar reserva"""
    import json

    try:
        reservation = get_object_or_404(StockReservation, id=reservation_id)

        if reservation.is_expired:
            return JsonResponse({
                'success': False,
                'message': 'Não é possível editar uma reserva expirada.'
            })

        data = json.loads(request.body)

        quantity = data.get('quantity')
        expiry_date = data.get('expiry_date')
        purpose = data.get('purpose')
        reference_document = data.get('reference_document', '')
        notes = data.get('notes', '')

        if quantity:
            new_quantity = Decimal(str(quantity))
            # Se aumentando quantidade, verificar estoque
            if new_quantity > reservation.quantity:
                difference = new_quantity - reservation.quantity
                try:
                    stock = MaterialStock.objects.get(
                        material=reservation.material,
                        warehouse=reservation.warehouse
                    )
                    # Verificar se há estoque disponível para o adicional
                    if stock.available_quantity < difference:
                        return JsonResponse({
                            'success': False,
                            'message': f'Estoque insuficiente para aumentar reserva. Disponível: {stock.available_quantity} kg'
                        })
                except MaterialStock.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Material não encontrado no estoque.'
                    })
            reservation.quantity = new_quantity

        if expiry_date:
            reservation.expiry_date = expiry_date
        if purpose:
            reservation.purpose = purpose
        reservation.reference_document = reference_document
        reservation.notes = notes
        reservation.updated_by = request.user
        reservation.save()

        return JsonResponse({
            'success': True,
            'message': 'Reserva atualizada com sucesso.'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dados inválidos.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao atualizar reserva: {str(e)}'
        })


@login_required
@require_http_methods(["DELETE"])
def reservation_cancel(request, reservation_id):
    """API: Cancelar reserva"""
    try:
        reservation = get_object_or_404(StockReservation, id=reservation_id)

        # Soft delete - marcar como inativa
        reservation.is_active = False
        reservation.updated_by = request.user
        reservation.save()

        return JsonResponse({
            'success': True,
            'message': 'Reserva cancelada com sucesso.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao cancelar reserva: {str(e)}'
        })
