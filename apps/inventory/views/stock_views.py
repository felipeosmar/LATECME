from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import (
    Warehouse, MaterialStock, StockMovement,
    StockReservation
)
from apps.materials.models import Material


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
