from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .models import (
    Warehouse, MaterialStock, StockMovement,
    StockReservation, InventoryCount, InventoryCountItem,
    ProductionOrder, Bin, BinHistory, Batch, BatchItem
)
from .forms import (
    ProductionOrderForm, BinForm, BinLoadForm, BatchForm
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
    
    # Dados para filtros
    warehouses = Warehouse.objects.filter(is_active=True)
    movement_types = StockMovement.MOVEMENT_TYPES
    
    context = {
        'movements': movements,
        'search': search,
        'warehouses': warehouses,
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


# =====================================================
# VIEWS PARA ORDENS DE PRODUÇÃO
# =====================================================

@login_required
def production_order_list(request):
    """Lista de ordens de produção"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    orders = ProductionOrder.objects.select_related(
        'material', 'responsible', 'created_by'
    ).prefetch_related('batches')

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(material__code__icontains=search) |
            Q(material__name__icontains=search)
        )

    if status:
        orders = orders.filter(status=status)

    orders = orders.order_by('-created_at')

    # Statistics
    stats = {
        'in_progress': ProductionOrder.objects.filter(status='IN_PROGRESS').count(),
        'completed': ProductionOrder.objects.filter(status='COMPLETED').count(),
        'total_batches': Batch.objects.count(),
    }

    paginator = Paginator(orders, 20)
    page = request.GET.get('page')
    orders = paginator.get_page(page)

    materials = Material.objects.filter(is_active=True)
    users = CustomUser.objects.filter(is_active=True, status='approved')

    context = {
        'orders': orders,
        'search': search,
        'status_filter': status,
        'status_choices': ProductionOrder.STATUS_CHOICES,
        'materials': materials,
        'users': users,
        'stats': stats,
    }

    return render(request, 'inventory/production_order_list.html', context)


@login_required
def production_order_detail(request, order_id):
    """Detalhes de uma ordem de produção"""
    order = get_object_or_404(ProductionOrder, id=order_id)
    batches = order.batches.select_related('material', 'prepared_by').prefetch_related('items')

    # Calculate totals and counts
    total_target = batches.aggregate(total=Sum('target_quantity'))['total'] or Decimal('0')
    batches_completed = batches.filter(status='COMPLETED').count()
    batches_in_progress = batches.filter(status='IN_PRODUCTION').count()
    batches_preparation = batches.filter(status__in=['PREPARATION', 'READY']).count()

    context = {
        'order': order,
        'batches': batches,
        'total_target': total_target,
        'batches_completed': batches_completed,
        'batches_in_progress': batches_in_progress,
        'batches_preparation': batches_preparation,
    }

    return render(request, 'inventory/production_order_detail.html', context)


@login_required
@require_http_methods(["POST"])
def production_order_create(request):
    """Criar nova ordem de produção via AJAX"""
    try:
        form = ProductionOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.updated_by = request.user
            order.save()

            return JsonResponse({
                'success': True,
                'message': 'Ordem de Produção criada com sucesso.',
                'data': {
                    'id': str(order.id),
                    'order_number': order.order_number
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro de validação.',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar ordem: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def production_order_start(request, order_id):
    """Iniciar ordem de produção"""
    order = get_object_or_404(ProductionOrder, id=order_id)

    if order.start(request.user):
        return JsonResponse({
            'success': True,
            'message': 'Ordem de Produção iniciada com sucesso.'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Não foi possível iniciar a ordem.'
        })


@login_required
@require_http_methods(["POST"])
def production_order_complete(request, order_id):
    """Concluir ordem de produção"""
    order = get_object_or_404(ProductionOrder, id=order_id)

    if order.complete(request.user):
        return JsonResponse({
            'success': True,
            'message': 'Ordem de Produção concluída com sucesso.'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Não foi possível concluir a ordem.'
        })


# =====================================================
# VIEWS PARA CONTENTORES (BINS)
# =====================================================

@login_required
def bin_list(request):
    """Lista de contentores"""
    search = request.GET.get('search', '')
    warehouse_id = request.GET.get('warehouse', '')
    status = request.GET.get('status', '')

    bins = Bin.objects.select_related('warehouse', 'current_material')

    if search:
        bins = bins.filter(
            Q(code__icontains=search) |
            Q(current_material__code__icontains=search) |
            Q(location_code__icontains=search)
        )

    if warehouse_id:
        bins = bins.filter(warehouse_id=warehouse_id)

    if status:
        bins = bins.filter(status=status)

    bins = bins.order_by('warehouse__code', 'code')

    paginator = Paginator(bins, 25)
    page = request.GET.get('page')
    bins = paginator.get_page(page)

    warehouses = Warehouse.objects.filter(is_active=True)
    materials = Material.objects.filter(is_active=True)

    context = {
        'bins': bins,
        'search': search,
        'warehouses': warehouses,
        'materials': materials,
        'warehouse_filter': warehouse_id,
        'status_filter': status,
        'status_choices': Bin.STATUS_CHOICES,
    }

    return render(request, 'inventory/bin_list.html', context)


@login_required
def bin_detail(request, bin_id):
    """Detalhes de um contentor"""
    bin_obj = get_object_or_404(Bin.objects.select_related(
        'warehouse', 'current_material'
    ), id=bin_id)

    # AJAX request para modal de edição
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'id': str(bin_obj.id),
            'code': bin_obj.code,
            'warehouse_id': str(bin_obj.warehouse.id),
            'status': bin_obj.status,
            'capacity': float(bin_obj.capacity) if bin_obj.capacity else None,
            'current_material_code': bin_obj.current_material.code if bin_obj.current_material else None,
            'current_quantity': float(bin_obj.current_quantity),
            'current_supplier_batch': bin_obj.current_supplier_batch,
            'current_certificate': bin_obj.current_certificate,
            'location_code': bin_obj.location_code,
            'notes': bin_obj.notes,
            'is_active': bin_obj.is_active
        })

    # Histórico recente
    recent_history = bin_obj.history.select_related(
        'material', 'batch', 'performed_by'
    ).order_by('-created_at')[:10]

    # Statistics
    history_stats = {
        'total_in': bin_obj.history.filter(movement_type='IN').count(),
        'total_out': bin_obj.history.filter(movement_type__in=['OUT', 'EMPTY']).count(),
        'total': bin_obj.history.count(),
    }

    materials = Material.objects.filter(is_active=True)

    context = {
        'bin': bin_obj,
        'recent_history': recent_history,
        'history_stats': history_stats,
        'materials': materials,
    }

    return render(request, 'inventory/bin_detail.html', context)


@login_required
@require_http_methods(["POST"])
def bin_create(request):
    """Criar novo contentor via AJAX"""
    try:
        form = BinForm(request.POST)
        if form.is_valid():
            bin_obj = form.save(commit=False)
            bin_obj.created_by = request.user
            bin_obj.updated_by = request.user
            bin_obj.save()

            return JsonResponse({
                'success': True,
                'message': 'Contentor criado com sucesso.',
                'bin_id': str(bin_obj.id)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro de validação.',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar contentor: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def bin_load(request, bin_id):
    """Carregar material em contentor via AJAX"""
    bin_obj = get_object_or_404(Bin, id=bin_id)

    try:
        form = BinLoadForm(request.POST)
        if form.is_valid():
            bin_obj.load_material(
                material=form.cleaned_data['material'],
                quantity=form.cleaned_data['quantity'],
                supplier_batch=form.cleaned_data.get('supplier_batch', ''),
                certificate=form.cleaned_data.get('certificate', ''),
                user=request.user
            )

            return JsonResponse({
                'success': True,
                'message': 'Material carregado com sucesso.',
                'current_quantity': float(bin_obj.current_quantity)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro de validação.',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def bin_empty(request, bin_id):
    """Esvaziar contentor via AJAX"""
    bin_obj = get_object_or_404(Bin, id=bin_id)
    notes = request.POST.get('notes', '')

    try:
        bin_obj.empty(user=request.user, notes=notes)

        return JsonResponse({
            'success': True,
            'message': 'Contentor esvaziado com sucesso.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def bin_history(request, bin_id):
    """Histórico completo do contentor"""
    bin_obj = get_object_or_404(Bin, id=bin_id)

    # Filters
    type_filter = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    history = bin_obj.history.select_related(
        'material', 'batch', 'performed_by'
    )

    if type_filter:
        history = history.filter(movement_type=type_filter)

    if date_from:
        history = history.filter(created_at__date__gte=date_from)

    if date_to:
        history = history.filter(created_at__date__lte=date_to)

    history = history.order_by('-created_at')

    # Statistics
    stats = {
        'total_in': bin_obj.history.filter(movement_type='IN').count(),
        'total_out': bin_obj.history.filter(movement_type__in=['OUT', 'EMPTY']).count(),
    }

    paginator = Paginator(history, 50)
    page = request.GET.get('page')
    history = paginator.get_page(page)

    context = {
        'bin': bin_obj,
        'history': history,
        'stats': stats,
        'type_filter': type_filter,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'inventory/bin_history.html', context)


# =====================================================
# VIEWS PARA BATELADAS (BATCHES)
# =====================================================

@login_required
def batch_list(request):
    """Lista de bateladas"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    order_id = request.GET.get('order', '')

    batches = Batch.objects.select_related(
        'production_order', 'material', 'prepared_by'
    ).prefetch_related('items')

    if search:
        batches = batches.filter(
            Q(batch_number__icontains=search) |
            Q(material__code__icontains=search) |
            Q(production_order__order_number__icontains=search)
        )

    if status:
        batches = batches.filter(status=status)

    if order_id:
        batches = batches.filter(production_order_id=order_id)

    batches = batches.order_by('-created_at')

    paginator = Paginator(batches, 20)
    page = request.GET.get('page')
    batches = paginator.get_page(page)

    production_orders = ProductionOrder.objects.filter(
        status__in=['PLANNED', 'IN_PROGRESS']
    ).select_related('material')
    materials = Material.objects.filter(is_active=True)

    context = {
        'batches': batches,
        'search': search,
        'status_filter': status,
        'order_filter': order_id,
        'status_choices': Batch.STATUS_CHOICES,
        'production_orders': production_orders,
        'materials': materials,
    }

    return render(request, 'inventory/batch_list.html', context)


@login_required
def batch_detail(request, batch_id):
    """Detalhes de uma batelada"""
    batch = get_object_or_404(Batch.objects.select_related(
        'production_order', 'material', 'prepared_by'
    ), id=batch_id)

    items = batch.items.select_related('bin', 'material', 'collected_by')

    # Contentores disponíveis para este material
    available_bins = Bin.objects.filter(
        current_material=batch.material,
        status='LOADED',
        is_active=True
    ).select_related('warehouse')

    context = {
        'batch': batch,
        'items': items,
        'available_bins': available_bins,
    }

    return render(request, 'inventory/batch_detail.html', context)


@login_required
@require_http_methods(["POST"])
def batch_create(request):
    """Criar nova batelada via AJAX"""
    try:
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.material = batch.production_order.material
            batch.created_by = request.user
            batch.updated_by = request.user
            batch.save()

            return JsonResponse({
                'success': True,
                'message': 'Batelada criada com sucesso.',
                'data': {
                    'id': str(batch.id),
                    'batch_number': batch.batch_number
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro de validação.',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar batelada: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def batch_add_bin(request, batch_id):
    """Adicionar material de contentor à batelada via AJAX"""
    batch = get_object_or_404(Batch, id=batch_id)

    try:
        bin_id = request.POST.get('bin') or request.POST.get('bin_id')
        quantity = Decimal(request.POST.get('quantity', '0'))

        bin_obj = get_object_or_404(Bin, id=bin_id)

        batch_item = batch.add_bin_material(
            bin_obj=bin_obj,
            quantity=quantity,
            user=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'Material adicionado do contentor {bin_obj.code}.',
            'item_id': str(batch_item.id),
            'actual_quantity': float(batch.actual_quantity)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def batch_mark_ready(request, batch_id):
    """Marcar batelada como pronta"""
    batch = get_object_or_404(Batch, id=batch_id)

    try:
        batch.mark_ready(request.user)
        return JsonResponse({
            'success': True,
            'message': 'Batelada marcada como pronta.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def batch_start_production(request, batch_id):
    """Iniciar produção com batelada"""
    batch = get_object_or_404(Batch, id=batch_id)

    try:
        batch.start_production(request.user)
        return JsonResponse({
            'success': True,
            'message': 'Produção iniciada.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def batch_complete(request, batch_id):
    """Concluir batelada"""
    batch = get_object_or_404(Batch, id=batch_id)

    try:
        batch.complete(request.user)
        return JsonResponse({
            'success': True,
            'message': 'Batelada concluída.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# =====================================================
# API ENDPOINTS
# =====================================================

@login_required
def api_bins_by_material(request, material_id):
    """Obter contentores disponíveis para um material (AJAX)"""
    bins = Bin.objects.filter(
        current_material_id=material_id,
        status='LOADED',
        is_active=True
    ).select_related('warehouse').values(
        'id', 'code', 'warehouse__code', 'current_quantity',
        'current_supplier_batch', 'current_certificate'
    )

    return JsonResponse({
        'success': True,
        'bins': list(bins)
    })