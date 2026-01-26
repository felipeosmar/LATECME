from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    # Ordens de Produção
    path('orders/', views.production_order_list, name='order_list'),
    path('orders/create/', views.production_order_create, name='order_create'),
    path('orders/<uuid:order_id>/', views.production_order_detail, name='order_detail'),
    path('orders/<uuid:order_id>/start/', views.production_order_start, name='order_start'),
    path('orders/<uuid:order_id>/complete/', views.production_order_complete, name='order_complete'),

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
