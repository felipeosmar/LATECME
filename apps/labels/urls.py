from django.urls import path
from . import views

app_name = 'labels'

urlpatterns = [
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/designer/', views.template_designer, name='template_designer'),
    path('templates/designer/<uuid:template_id>/', views.template_designer, name='template_designer_edit'),
    path('templates/save/', views.template_save, name='template_save'),
    path('templates/delete/<uuid:template_id>/', views.template_delete, name='template_delete'),

    # Impressão
    path('print/', views.quick_print, name='quick_print'),
    path('print/form/<uuid:bin_id>/', views.print_form, name='print_form'),
    path('print/preview/<uuid:bin_id>/<uuid:template_id>/', views.print_preview, name='print_preview'),
    path('print/execute/', views.print_label, name='print_label'),

    # Impressoras
    path('printers/', views.printer_list, name='printer_list'),
    path('printers/<uuid:printer_id>/test/', views.printer_test, name='printer_test'),

    # Histórico de impressão
    path('jobs/', views.print_job_list, name='print_job_list'),
]
