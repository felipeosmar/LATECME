from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Solicitacoes de Compra
    path('requests/', views.request_list, name='request_list'),
    path('requests/create/', views.request_create, name='request_create'),
    path('requests/<uuid:request_id>/', views.request_detail, name='request_detail'),
    path('requests/<uuid:request_id>/update/', views.request_update, name='request_update'),
    path('requests/<uuid:request_id>/submit/', views.request_submit, name='request_submit'),
    path('requests/<uuid:request_id>/approve/', views.request_approve, name='request_approve'),
    path('requests/<uuid:request_id>/reject/', views.request_reject, name='request_reject'),
    path('requests/<uuid:request_id>/items/add/', views.request_item_add, name='request_item_add'),
    path('requests/<uuid:request_id>/items/<uuid:item_id>/remove/', views.request_item_remove, name='request_item_remove'),

    # Pedidos de Compra
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<uuid:order_id>/send/', views.order_send, name='order_send'),
    path('orders/<uuid:order_id>/confirm/', views.order_confirm, name='order_confirm'),
    path('orders/<uuid:order_id>/items/add/', views.order_item_add, name='order_item_add'),
    path('orders/<uuid:order_id>/items/<uuid:item_id>/remove/', views.order_item_remove, name='order_item_remove'),

    # Recebimentos
    path('receivings/', views.receiving_list, name='receiving_list'),
    path('receivings/create/', views.receiving_create, name='receiving_create'),
    path('receivings/<uuid:receiving_id>/', views.receiving_detail, name='receiving_detail'),
    path('receivings/<uuid:receiving_id>/items/add/', views.receiving_item_add, name='receiving_item_add'),
    path('receivings/<uuid:receiving_id>/approve/', views.receiving_approve, name='receiving_approve'),
    path('receivings/<uuid:receiving_id>/reject/', views.receiving_reject, name='receiving_reject'),

    # API Endpoints
    path('api/approved-requests/', views.api_approved_requests, name='api_approved_requests'),
    path('api/orders/<uuid:order_id>/items/', views.api_order_items, name='api_order_items'),
]
