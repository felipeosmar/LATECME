from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import (
    PurchaseRequest,
    PurchaseOrder,
    Receiving
)


@login_required
def dashboard(request):
    """Dashboard de compras"""
    # Estatisticas
    stats = {
        'pending_requests': PurchaseRequest.objects.filter(status='PENDING').count(),
        'approved_requests': PurchaseRequest.objects.filter(status='APPROVED').count(),
        'open_orders': PurchaseOrder.objects.filter(status__in=['SENT', 'CONFIRMED', 'PARTIAL']).count(),
        'pending_receivings': Receiving.objects.filter(status='PENDING').count(),
    }

    # Solicitacoes pendentes de aprovacao
    pending_requests = PurchaseRequest.objects.filter(
        status='PENDING'
    ).select_related('requester', 'warehouse').order_by('-request_date')[:5]

    # Pedidos aguardando recebimento
    pending_orders = PurchaseOrder.objects.filter(
        status__in=['SENT', 'CONFIRMED', 'PARTIAL']
    ).select_related('supplier', 'warehouse').order_by('expected_delivery_date')[:5]

    # Recebimentos pendentes de inspecao
    pending_inspections = Receiving.objects.filter(
        status='PENDING'
    ).select_related('purchase_order', 'received_by').order_by('-receiving_date')[:5]

    context = {
        'stats': stats,
        'pending_requests': pending_requests,
        'pending_orders': pending_orders,
        'pending_inspections': pending_inspections,
    }

    return render(request, 'purchasing/dashboard.html', context)
