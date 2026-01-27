from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..models import Warehouse, MaterialStock, StockMovement
from apps.accounts.models import CustomUser
from django.db.models import F


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
