from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_materials, name='dashboard'),
    
    # Materiais
    path('list/', views.material_list, name='list'),
    path('detail/<uuid:material_id>/', views.material_detail, name='detail'),
    path('create/', views.material_create, name='create'),
    path('edit/<uuid:material_id>/', views.material_edit, name='edit'),
    
    # Fornecedores
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/detail/<uuid:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/edit/<uuid:supplier_id>/', views.supplier_edit, name='supplier_edit'),
    
    # API
    path('api/search/', views.material_search_api, name='search_api'),
]