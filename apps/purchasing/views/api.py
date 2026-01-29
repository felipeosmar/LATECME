from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..models import PurchaseRequest, PurchaseOrder


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
