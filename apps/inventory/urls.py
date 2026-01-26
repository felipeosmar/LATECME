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
]
