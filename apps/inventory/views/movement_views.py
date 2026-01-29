from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..models import Warehouse, MaterialStock, StockMovement
from apps.materials.models import Material
from datetime import datetime
from decimal import Decimal


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
