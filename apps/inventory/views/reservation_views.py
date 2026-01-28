from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ..models import (
    Warehouse, MaterialStock, StockMovement,
    StockReservation, InventoryCount, InventoryCountItem
)
from apps.materials.models import Material
from apps.accounts.models import CustomUser
from datetime import datetime, timedelta
from decimal import Decimal


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
