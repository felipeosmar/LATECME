from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
import json

from .models import LabelTemplate, PrinterConfiguration, PrintJob
from apps.production.models import Bin
from .epl_generator import EPLGenerator
from .printer_client import PrinterClient


@login_required
def template_list(request):
    """Lista todos os templates de etiquetas"""
    templates = LabelTemplate.objects.filter(is_active=True).order_by('-is_default', 'name')
    context = {
        'templates': templates,
    }
    return render(request, 'labels/template_list.html', context)


@login_required
def template_designer(request, template_id=None):
    """Interface do designer de etiquetas"""
    template = None
    if template_id:
        template = get_object_or_404(LabelTemplate, id=template_id, is_active=True)

    context = {
        'template': template,
        'template_json': json.dumps(template.template_json) if template else '{}',
    }
    return render(request, 'labels/designer.html', context)


@login_required
@require_http_methods(["POST"])
def template_save(request):
    """Salva ou atualiza um template (AJAX)"""
    try:
        data = json.loads(request.body)

        template_id = data.get('template_id')
        name = data.get('name')
        description = data.get('description', '')
        width_mm = data.get('width_mm')
        height_mm = data.get('height_mm')
        printer_dpi = data.get('printer_dpi', 203)
        template_json = data.get('template_json', {})
        is_default = data.get('is_default', False)

        # Validação básica
        if not name or not width_mm or not height_mm:
            return JsonResponse({
                'success': False,
                'error': 'Nome, largura e altura são obrigatórios'
            }, status=400)

        # Criar ou atualizar template
        if template_id:
            template = get_object_or_404(LabelTemplate, id=template_id)
            template.name = name
            template.description = description
            template.width_mm = width_mm
            template.height_mm = height_mm
            template.printer_dpi = printer_dpi
            template.template_json = template_json
            template.is_default = is_default
            template.updated_by = request.user
        else:
            template = LabelTemplate(
                name=name,
                description=description,
                width_mm=width_mm,
                height_mm=height_mm,
                printer_dpi=printer_dpi,
                template_json=template_json,
                is_default=is_default,
                created_by=request.user,
                updated_by=request.user
            )

        template.save()

        return JsonResponse({
            'success': True,
            'template_id': str(template.id),
            'message': 'Template salvo com sucesso'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def template_delete(request, template_id):
    """Deleta um template (soft delete)"""
    template = get_object_or_404(LabelTemplate, id=template_id)
    template.is_active = False
    template.updated_by = request.user
    template.save()

    messages.success(request, f'Template "{template.name}" removido com sucesso.')
    return redirect('labels:template_list')


@login_required
def print_form(request, bin_id):
    """Formulário para seleção de template e impressora"""
    bin_obj = get_object_or_404(Bin, id=bin_id, is_active=True)

    templates = LabelTemplate.objects.filter(is_active=True).order_by('-is_default', 'name')
    printers = PrinterConfiguration.objects.filter(is_active=True).order_by('-is_default', 'name')

    # Pre-selecionar padrões
    default_template = templates.filter(is_default=True).first()
    default_printer = printers.filter(is_default=True).first()

    context = {
        'bin': bin_obj,
        'templates': templates,
        'printers': printers,
        'default_template': default_template,
        'default_printer': default_printer,
    }
    return render(request, 'labels/print_form.html', context)


@login_required
def print_preview(request, bin_id, template_id):
    """Preview da etiqueta antes de imprimir"""
    bin_obj = get_object_or_404(Bin, id=bin_id, is_active=True)
    template = get_object_or_404(LabelTemplate, id=template_id, is_active=True)

    # Gerar EPL
    generator = EPLGenerator(template, bin_obj)
    epl_content = generator.generate()

    context = {
        'bin': bin_obj,
        'template': template,
        'epl_content': epl_content,
    }
    return render(request, 'labels/print_preview.html', context)


@login_required
@require_http_methods(["POST"])
def print_label(request):
    """Executa impressão da etiqueta (AJAX)"""
    try:
        data = json.loads(request.body)

        bin_id = data.get('bin_id')
        template_id = data.get('template_id')
        printer_id = data.get('printer_id')

        # Validação
        if not bin_id or not template_id or not printer_id:
            return JsonResponse({
                'success': False,
                'error': 'Bin, template e impressora são obrigatórios'
            }, status=400)

        # Obter objetos
        bin_obj = get_object_or_404(Bin, id=bin_id, is_active=True)
        template = get_object_or_404(LabelTemplate, id=template_id, is_active=True)
        printer = get_object_or_404(PrinterConfiguration, id=printer_id, is_active=True)

        # Gerar EPL
        generator = EPLGenerator(template, bin_obj)
        epl_content = generator.generate()
        bin_snapshot = generator.get_bin_snapshot()

        # Criar PrintJob
        print_job = PrintJob(
            printer=printer,
            template=template,
            bin=bin_obj,
            status='PROCESSING',
            epl_content=epl_content,
            bin_data_snapshot=bin_snapshot,
            created_by=request.user,
            updated_by=request.user
        )
        print_job.save()

        # Enviar para impressora
        client = PrinterClient(printer)
        success, error_message = client.send_epl(epl_content)

        # Atualizar PrintJob
        if success:
            print_job.status = 'SUCCESS'
            print_job.printed_at = timezone.now()
        else:
            print_job.status = 'FAILED'
            print_job.error_message = error_message

        print_job.save()

        return JsonResponse({
            'success': success,
            'print_job_id': str(print_job.id),
            'message': 'Etiqueta impressa com sucesso' if success else error_message
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def printer_list(request):
    """Lista todas as impressoras configuradas"""
    printers = PrinterConfiguration.objects.filter(is_active=True).order_by('-is_default', 'name')
    context = {
        'printers': printers,
    }
    return render(request, 'labels/printer_list.html', context)


@login_required
@require_http_methods(["POST"])
def printer_test(request, printer_id):
    """Testa conexão com impressora (AJAX)"""
    try:
        printer = get_object_or_404(PrinterConfiguration, id=printer_id, is_active=True)

        client = PrinterClient(printer)
        success, message = client.test_connection()

        return JsonResponse({
            'success': success,
            'message': message
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def print_job_list(request):
    """Lista histórico de trabalhos de impressão"""
    jobs = PrintJob.objects.filter(
        is_active=True
    ).select_related(
        'printer', 'template', 'bin', 'created_by'
    ).order_by('-created_at')[:100]  # Últimos 100

    context = {
        'jobs': jobs,
    }
    return render(request, 'labels/print_job_list.html', context)
