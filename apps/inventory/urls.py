from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Estoques
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/<uuid:stock_id>/', views.stock_detail, name='stock_detail'),
    
    # Movimentações
    path('movements/', views.movements_list, name='movements_list'),
    path('movements/create/', views.create_movement, name='create_movement'),
    
    # Armazéns
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouses/<uuid:warehouse_id>/', views.warehouse_detail, name='warehouse_detail'),
    path('warehouses/<uuid:warehouse_id>/update/', views.warehouse_update, name='warehouse_update'),
    
    # Reservas
    path('reservations/', views.reservations_list, name='reservations_list'),

    # Relatórios
    path('reports/', views.reports, name='reports'),

    # Ordens de Produção
    path('production-orders/', views.production_order_list, name='production_order_list'),
    path('production-orders/create/', views.production_order_create, name='production_order_create'),
    path('production-orders/<uuid:order_id>/', views.production_order_detail, name='production_order_detail'),
    path('production-orders/<uuid:order_id>/start/', views.production_order_start, name='production_order_start'),
    path('production-orders/<uuid:order_id>/complete/', views.production_order_complete, name='production_order_complete'),

    # Contentores (Bins)
    path('bins/', views.bin_list, name='bin_list'),
    path('bins/create/', views.bin_create, name='bin_create'),
    path('bins/<uuid:bin_id>/', views.bin_detail, name='bin_detail'),
    path('bins/<uuid:bin_id>/load/', views.bin_load, name='bin_load'),
    path('bins/<uuid:bin_id>/empty/', views.bin_empty, name='bin_empty'),
    path('bins/<uuid:bin_id>/history/', views.bin_history, name='bin_history'),

    # Bateladas (Batches)
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),
    path('batches/<uuid:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batches/<uuid:batch_id>/add-bin/', views.batch_add_bin, name='batch_add_bin'),
    path('batches/<uuid:batch_id>/mark-ready/', views.batch_mark_ready, name='batch_mark_ready'),
    path('batches/<uuid:batch_id>/start-production/', views.batch_start_production, name='batch_start_production'),
    path('batches/<uuid:batch_id>/complete/', views.batch_complete, name='batch_complete'),

    # API
    path('api/bins/by-material/<uuid:material_id>/', views.api_bins_by_material, name='api_bins_by_material'),
]