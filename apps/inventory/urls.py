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
    path('reservations/create/', views.reservation_create, name='reservation_create'),
    path('reservations/<uuid:reservation_id>/', views.reservation_detail, name='reservation_detail'),
    path('reservations/<uuid:reservation_id>/update/', views.reservation_update, name='reservation_update'),
    path('reservations/<uuid:reservation_id>/cancel/', views.reservation_cancel, name='reservation_cancel'),

    # Contagens de Inventário
    path('counts/', views.inventory_count_list, name='inventory_count_list'),
    path('counts/create/', views.inventory_count_create, name='inventory_count_create'),
    path('counts/<uuid:count_id>/', views.inventory_count_detail, name='inventory_count_detail'),
    path('counts/<uuid:count_id>/start/', views.inventory_count_start, name='inventory_count_start'),
    path('counts/<uuid:count_id>/save-items/', views.inventory_count_save_items, name='inventory_count_save_items'),
    path('counts/<uuid:count_id>/complete/', views.inventory_count_complete, name='inventory_count_complete'),
    path('counts/<uuid:count_id>/cancel/', views.inventory_count_cancel, name='inventory_count_cancel'),
    path('counts/<uuid:count_id>/generate-adjustments/', views.inventory_count_generate_adjustments, name='inventory_count_generate_adjustments'),

    # API Endpoints
    path('api/materials-with-stock/', views.api_materials_with_stock, name='api_materials_with_stock'),
    path('api/warehouses/', views.api_warehouses, name='api_warehouses'),
    path('api/stock/<uuid:material_id>/<uuid:warehouse_id>/', views.api_stock_info, name='api_stock_info'),

    # Relatórios
    path('reports/', views.reports, name='reports'),
]
