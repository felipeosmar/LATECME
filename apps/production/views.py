from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from decimal import Decimal

from .models import ProductionOrder, Bin, BinHistory, Batch, BatchItem
from .forms import ProductionOrderForm, BinForm, BinLoadForm, BatchForm
from apps.materials.models import Material
from apps.accounts.models import CustomUser
from apps.inventory.models import Warehouse


# =====================================================
# VIEWS PARA ORDENS DE PRODUÇÃO
# =====================================================

@login_required
def production_order_list(request):
    """Lista de ordens de produção"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    orders = ProductionOrder.objects.select_related(
        'material', 'responsible', 'created_by'
    ).prefetch_related('batches')

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(material__code__icontains=search) |
            Q(material__name__icontains=search)
        )

    if status:
        orders = orders.filter(status=status)

    orders = orders.order_by('-created_at')

    # Statistics
    stats = {
        'in_progress': ProductionOrder.objects.filter(status='IN_PROGRESS').count(),
        'completed': ProductionOrder.objects.filter(status='COMPLETED').count(),
        'total_batches': Batch.objects.count(),
    }

    paginator = Paginator(orders, 20)
    page = request.GET.get('page')
    orders = paginator.get_page(page)

    materials = Material.objects.filter(is_active=True)
    users = CustomUser.objects.filter(is_active=True, status='approved')

    context = {
        'orders': orders,
        'search': search,
        'status_filter': status,
        'status_choices': ProductionOrder.STATUS_CHOICES,
        'materials': materials,
        'users': users,
        'stats': stats,
    }

    return render(request, 'production/production_order_list.html', context)


@login_required
def production_order_detail(request, order_id):
    """Detalhes de uma ordem de produção"""
    order = get_object_or_404(ProductionOrder, id=order_id)
    batches = order.batches.select_related('material', 'prepared_by').prefetch_related('items')

    # Calculate totals and counts
    total_target = batches.aggregate(total=Sum('target_quantity'))['total'] or Decimal('0')
    batches_completed = batches.filter(status='COMPLETED').count()
    batches_in_progress = batches.filter(status='IN_PRODUCTION').count()
    batches_preparation = batches.filter(status__in=['PREPARATION', 'READY']).count()

    context = {
        'order': order,
        'batches': batches,
        'total_target': total_target,
        'batches_completed': batches_completed,
        'batches_in_progress': batches_in_progress,
        'batches_preparation': batches_preparation,
    }

    return render(request, 'production/production_order_detail.html', context)


@login_required
@require_http_methods(["POST"])
def production_order_create(request):
    """Criar nova ordem de produção via AJAX"""
    try:
        form = ProductionOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.updated_by = request.user
            order.save()

            return JsonResponse({
                'success': True,
                'message': 'Ordem de Produção criada com sucesso.',
                'data': {
                    'id': str(order.id),
                    'order_number': order.order_number
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro de validação.',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar ordem: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def production_order_start(request, order_id):
    """Iniciar ordem de produção"""
    order = get_object_or_404(ProductionOrder, id=order_id)

    if order.start(request.user):
        return JsonResponse({
            'success': True,
            'message': 'Ordem de Produção iniciada com sucesso.'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Não foi possível iniciar a ordem.'
        })


@login_required
@require_http_methods(["POST"])
def production_order_complete(request, order_id):
    """Concluir ordem de produção"""
    order = get_object_or_404(ProductionOrder, id=order_id)

    if order.complete(request.user):
        return JsonResponse({
            'success': True,
            'message': 'Ordem de Produção concluída com sucesso.'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Não foi possível concluir a ordem.'
        })


# =====================================================
# VIEWS PARA OPERAÇÕES EM LOTE DE ORDENS DE PRODUÇÃO
# =====================================================

@login_required
@require_http_methods(["POST"])
def production_order_batch_start(request):
    """Iniciar múltiplas ordens de produção em lote via AJAX"""
    try:
        import json

        # Parse JSON data from request body
        try:
            data = json.loads(request.body)
            order_ids = data.get('order_ids', [])
        except json.JSONDecodeError:
            # Fallback to POST data if JSON parsing fails
            order_ids = request.POST.getlist('order_ids[]')

        # Validações
        if not order_ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhuma ordem selecionada.'
            }, status=400)

        if len(order_ids) > 100:
            return JsonResponse({
                'success': False,
                'message': 'Máximo de 100 ordens por vez.'
            }, status=400)

        # Processar ordens em transação atômica
        started_count = 0
        failed_count = 0
        errors = []

        with transaction.atomic():
            for order_id in order_ids:
                try:
                    order = ProductionOrder.objects.get(id=order_id)
                    if order.start(request.user):
                        started_count += 1
                    else:
                        failed_count += 1
                        errors.append(f'Ordem {order.order_number}: não foi possível iniciar (status atual: {order.get_status_display()})')
                except ProductionOrder.DoesNotExist:
                    failed_count += 1
                    errors.append(f'Ordem {order_id}: não encontrada')
                except Exception as e:
                    failed_count += 1
                    errors.append(f'Ordem {order_id}: {str(e)}')

        # Mensagem de retorno
        if started_count > 0 and failed_count == 0:
            message = f'{started_count} ordem(ns) iniciada(s) com sucesso.'
        elif started_count > 0 and failed_count > 0:
            message = f'{started_count} ordem(ns) iniciada(s), {failed_count} falharam.'
        else:
            message = f'Nenhuma ordem foi iniciada. {failed_count} falharam.'

        return JsonResponse({
            'success': started_count > 0,
            'message': message,
            'started': started_count,
            'failed': failed_count,
            'errors': errors
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': f'Valor inválido: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao iniciar ordens: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def production_order_batch_complete(request):
    """Concluir múltiplas ordens de produção em lote via AJAX"""
    try:
        import json

        # Parse JSON data from request body
        try:
            data = json.loads(request.body)
            order_ids = data.get('order_ids', [])
        except json.JSONDecodeError:
            # Fallback to POST data if JSON parsing fails
            order_ids = request.POST.getlist('order_ids[]')

        # Validações
        if not order_ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhuma ordem selecionada.'
            }, status=400)

        if len(order_ids) > 100:
            return JsonResponse({
                'success': False,
                'message': 'Máximo de 100 ordens por vez.'
            }, status=400)

        # Processar ordens em transação atômica
        completed_count = 0
        failed_count = 0
        errors = []

        with transaction.atomic():
            for order_id in order_ids:
                try:
                    order = ProductionOrder.objects.get(id=order_id)
                    if order.complete(request.user):
                        completed_count += 1
                    else:
                        failed_count += 1
                        errors.append(f'Ordem {order.order_number}: não foi possível concluir (status atual: {order.get_status_display()})')
                except ProductionOrder.DoesNotExist:
                    failed_count += 1
                    errors.append(f'Ordem {order_id}: não encontrada')
                except Exception as e:
                    failed_count += 1
                    errors.append(f'Ordem {order_id}: {str(e)}')

        # Mensagem de retorno
        if completed_count > 0 and failed_count == 0:
            message = f'{completed_count} ordem(ns) concluída(s) com sucesso.'
        elif completed_count > 0 and failed_count > 0:
            message = f'{completed_count} ordem(ns) concluída(s), {failed_count} falharam.'
        else:
            message = f'Nenhuma ordem foi concluída. {failed_count} falharam.'

        return JsonResponse({
            'success': completed_count > 0,
            'message': message,
            'completed': completed_count,
            'failed': failed_count,
            'errors': errors
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': f'Valor inválido: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao concluir ordens: {str(e)}'
        }, status=500)


# =====================================================
# VIEWS PARA CONTENTORES (BINS)
# =====================================================

@login_required
def bin_list(request):
    """Lista de contentores"""
    search = request.GET.get('search', '')
    warehouse_id = request.GET.get('warehouse', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    bins = Bin.objects.select_related('warehouse', 'current_material')

    if search:
        bins = bins.filter(
            Q(code__icontains=search) |
            Q(current_material__code__icontains=search) |
            Q(location_code__icontains=search)
        )

    if warehouse_id:
        bins = bins.filter(warehouse_id=warehouse_id)

    if status:
        bins = bins.filter(status=status)

    if date_from:
        bins = bins.filter(created_at__date__gte=date_from)

    if date_to:
        bins = bins.filter(created_at__date__lte=date_to)

    bins = bins.order_by('warehouse__code', 'code')

    paginator = Paginator(bins, 25)
    page = request.GET.get('page')
    bins = paginator.get_page(page)

    warehouses = Warehouse.objects.filter(is_active=True)
    materials = Material.objects.filter(is_active=True)

    # Dados para impressão em lote
    from apps.labels.models import LabelTemplate, PrinterConfiguration
    templates = LabelTemplate.objects.filter(is_active=True).order_by('-is_default', 'name')
    printers = PrinterConfiguration.objects.filter(is_active=True).order_by('-is_default', 'name')
    default_template = templates.filter(is_default=True).first()
    default_printer = printers.filter(is_default=True).first()

    context = {
        'bins': bins,
        'search': search,
        'warehouses': warehouses,
        'materials': materials,
        'warehouse_filter': warehouse_id,
        'status_filter': status,
        'status_choices': Bin.STATUS_CHOICES,
        'date_from': date_from,
        'date_to': date_to,
        # Dados para impressão em lote
        'templates': templates,
        'printers': printers,
        'default_template': default_template,
        'default_printer': default_printer,
    }

    return render(request, 'production/bin_list.html', context)


@login_required
def bin_detail(request, bin_id):
    """Detalhes de um contentor"""
    bin_obj = get_object_or_404(Bin.objects.select_related(
        'warehouse', 'current_material'
    ), id=bin_id)

    # AJAX request para modal de edição
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'id': str(bin_obj.id),
            'code': bin_obj.code,
            'warehouse_id': str(bin_obj.warehouse.id),
            'status': bin_obj.status,
            'capacity': float(bin_obj.capacity) if bin_obj.capacity else None,
            'current_material_code': bin_obj.current_material.code if bin_obj.current_material else None,
            'current_quantity': float(bin_obj.current_quantity),
            'current_supplier_batch': bin_obj.current_supplier_batch,
            'current_certificate': bin_obj.current_certificate,
            'location_code': bin_obj.location_code,
            'notes': bin_obj.notes,
            'is_active': bin_obj.is_active
        })

    # Histórico recente
    recent_history = bin_obj.history.select_related(
        'material', 'batch', 'performed_by'
    ).order_by('-created_at')[:10]

    # Statistics
    history_stats = {
        'total_in': bin_obj.history.filter(movement_type='IN').count(),
        'total_out': bin_obj.history.filter(movement_type__in=['OUT', 'EMPTY']).count(),
        'total': bin_obj.history.count(),
    }

    materials = Material.objects.filter(is_active=True)

    context = {
        'bin': bin_obj,
        'recent_history': recent_history,
        'history_stats': history_stats,
        'materials': materials,
    }

    return render(request, 'production/bin_detail.html', context)


@login_required
@require_http_methods(["POST"])
def bin_create(request):
    """Criar novo contentor via AJAX"""
    try:
        form = BinForm(request.POST)
        if form.is_valid():
            bin_obj = form.save(commit=False)
            bin_obj.created_by = request.user
            bin_obj.updated_by = request.user
            bin_obj.save()

            return JsonResponse({
                'success': True,
                'message': 'Contentor criado com sucesso.',
                'bin_id': str(bin_obj.id)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro de validação.',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar contentor: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def bin_load(request, bin_id):
    """Carregar material em contentor via AJAX"""
    bin_obj = get_object_or_404(Bin, id=bin_id)

    try:
        form = BinLoadForm(request.POST)
        if form.is_valid():
            bin_obj.load_material(
                material=form.cleaned_data['material'],
                quantity=form.cleaned_data['quantity'],
                supplier_batch=form.cleaned_data.get('supplier_batch', ''),
                certificate=form.cleaned_data.get('certificate', ''),
                user=request.user
            )

            return JsonResponse({
                'success': True,
                'message': 'Material carregado com sucesso.',
                'current_quantity': float(bin_obj.current_quantity)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro de validação.',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def bin_empty(request, bin_id):
    """Esvaziar contentor via AJAX"""
    bin_obj = get_object_or_404(Bin, id=bin_id)
    notes = request.POST.get('notes', '')

    try:
        bin_obj.empty(user=request.user, notes=notes)

        return JsonResponse({
            'success': True,
            'message': 'Contentor esvaziado com sucesso.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def bin_history(request, bin_id):
    """Histórico completo do contentor"""
    bin_obj = get_object_or_404(Bin, id=bin_id)

    # Filters
    type_filter = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    history = bin_obj.history.select_related(
        'material', 'batch', 'performed_by'
    )

    if type_filter:
        history = history.filter(movement_type=type_filter)

    if date_from:
        history = history.filter(created_at__date__gte=date_from)

    if date_to:
        history = history.filter(created_at__date__lte=date_to)

    history = history.order_by('-created_at')

    # Statistics
    stats = {
        'total_in': bin_obj.history.filter(movement_type='IN').count(),
        'total_out': bin_obj.history.filter(movement_type__in=['OUT', 'EMPTY']).count(),
    }

    paginator = Paginator(history, 50)
    page = request.GET.get('page')
    history = paginator.get_page(page)

    context = {
        'bin': bin_obj,
        'history': history,
        'stats': stats,
        'type_filter': type_filter,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'production/bin_history.html', context)


# =====================================================
# VIEWS PARA BATELADAS (BATCHES)
# =====================================================

@login_required
def batch_list(request):
    """Lista de bateladas"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    order_id = request.GET.get('order', '')

    batches = Batch.objects.select_related(
        'production_order', 'material', 'prepared_by'
    ).prefetch_related('items')

    if search:
        batches = batches.filter(
            Q(batch_number__icontains=search) |
            Q(material__code__icontains=search) |
            Q(production_order__order_number__icontains=search)
        )

    if status:
        batches = batches.filter(status=status)

    if order_id:
        batches = batches.filter(production_order_id=order_id)

    batches = batches.order_by('-created_at')

    paginator = Paginator(batches, 20)
    page = request.GET.get('page')
    batches = paginator.get_page(page)

    production_orders = ProductionOrder.objects.filter(
        status__in=['PLANNED', 'IN_PROGRESS']
    ).select_related('material')
    materials = Material.objects.filter(is_active=True)

    context = {
        'batches': batches,
        'search': search,
        'status_filter': status,
        'order_filter': order_id,
        'status_choices': Batch.STATUS_CHOICES,
        'production_orders': production_orders,
        'materials': materials,
    }

    return render(request, 'production/batch_list.html', context)


@login_required
def batch_detail(request, batch_id):
    """Detalhes de uma batelada"""
    batch = get_object_or_404(Batch.objects.select_related(
        'production_order', 'material', 'prepared_by'
    ), id=batch_id)

    items = batch.items.select_related('bin', 'material', 'collected_by')

    # Contentores disponíveis para este material
    available_bins = Bin.objects.filter(
        current_material=batch.material,
        status='LOADED',
        is_active=True
    ).select_related('warehouse')

    context = {
        'batch': batch,
        'items': items,
        'available_bins': available_bins,
    }

    return render(request, 'production/batch_detail.html', context)


@login_required
@require_http_methods(["POST"])
def batch_create(request):
    """Criar nova batelada via AJAX"""
    try:
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.material = batch.production_order.material
            batch.created_by = request.user
            batch.updated_by = request.user
            batch.save()

            return JsonResponse({
                'success': True,
                'message': 'Batelada criada com sucesso.',
                'data': {
                    'id': str(batch.id),
                    'batch_number': batch.batch_number
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro de validação.',
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar batelada: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def batch_add_bin(request, batch_id):
    """Adicionar material de contentor à batelada via AJAX"""
    batch = get_object_or_404(Batch, id=batch_id)

    try:
        bin_id = request.POST.get('bin') or request.POST.get('bin_id')
        quantity = Decimal(request.POST.get('quantity', '0'))

        bin_obj = get_object_or_404(Bin, id=bin_id)

        batch_item = batch.add_bin_material(
            bin_obj=bin_obj,
            quantity=quantity,
            user=request.user
        )

        return JsonResponse({
            'success': True,
            'message': f'Material adicionado do contentor {bin_obj.code}.',
            'item_id': str(batch_item.id),
            'actual_quantity': float(batch.actual_quantity)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def batch_mark_ready(request, batch_id):
    """Marcar batelada como pronta"""
    batch = get_object_or_404(Batch, id=batch_id)

    try:
        batch.mark_ready(request.user)
        return JsonResponse({
            'success': True,
            'message': 'Batelada marcada como pronta.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def batch_start_production(request, batch_id):
    """Iniciar produção com batelada"""
    batch = get_object_or_404(Batch, id=batch_id)

    try:
        batch.start_production(request.user)
        return JsonResponse({
            'success': True,
            'message': 'Produção iniciada.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def batch_complete(request, batch_id):
    """Concluir batelada"""
    batch = get_object_or_404(Batch, id=batch_id)

    try:
        batch.complete(request.user)
        return JsonResponse({
            'success': True,
            'message': 'Batelada concluída.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# =====================================================
# API ENDPOINTS
# =====================================================

@login_required
def api_bins_by_material(request, material_id):
    """Obter contentores disponíveis para um material (AJAX)"""
    bins = Bin.objects.filter(
        current_material_id=material_id,
        status='LOADED',
        is_active=True
    ).select_related('warehouse').values(
        'id', 'code', 'warehouse__code', 'current_quantity',
        'current_supplier_batch', 'current_certificate'
    )

    return JsonResponse({
        'success': True,
        'bins': list(bins)
    })


# =====================================================
# VIEWS PARA CRIAÇÃO E IMPRESSÃO EM LOTE
# =====================================================

@login_required
@require_http_methods(["POST"])
def bin_batch_create(request):
    """Criar múltiplos contentores em lote via AJAX"""
    try:
        # Obter dados do formulário
        warehouse_id = request.POST.get('warehouse')
        quantity = int(request.POST.get('quantity', 0))
        capacity = request.POST.get('capacity')
        location_code = request.POST.get('location_code', '')
        notes = request.POST.get('notes', '')
        auto_print = request.POST.get('auto_print') == 'true'
        printer_id = request.POST.get('printer_id')
        template_id = request.POST.get('template_id')

        # Validações
        if not warehouse_id:
            return JsonResponse({
                'success': False,
                'message': 'Armazém é obrigatório.'
            }, status=400)

        if quantity < 1 or quantity > 100:
            return JsonResponse({
                'success': False,
                'message': 'Quantidade deve ser entre 1 e 100.'
            }, status=400)

        warehouse = get_object_or_404(Warehouse, id=warehouse_id, is_active=True)

        # Converter capacidade
        capacity_decimal = None
        if capacity:
            capacity_decimal = Decimal(capacity)

        # Criar contentores em transação atômica
        created_bins = []
        with transaction.atomic():
            for _ in range(quantity):
                bin_obj = Bin(
                    warehouse=warehouse,
                    capacity=capacity_decimal,
                    location_code=location_code,
                    notes=notes,
                    status='EMPTY',
                    created_by=request.user,
                    updated_by=request.user
                )
                bin_obj.save()
                created_bins.append({
                    'id': str(bin_obj.id),
                    'code': bin_obj.code
                })

        # Impressão automática se solicitada
        print_status = {'success': True, 'printed': 0, 'errors': []}
        if auto_print and printer_id and template_id:
            print_status = _print_bin_labels(
                [b['id'] for b in created_bins],
                printer_id,
                template_id,
                request.user
            )

        return JsonResponse({
            'success': True,
            'message': f'{len(created_bins)} contentor(es) criado(s) com sucesso.',
            'bins_created': created_bins,
            'print_status': print_status
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': f'Valor inválido: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar contentores: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def bin_batch_print(request):
    """Imprimir etiquetas de múltiplos contentores via AJAX"""
    try:
        import json
        data = json.loads(request.body) if request.content_type == 'application/json' else None

        if data:
            bin_ids = data.get('bin_ids', [])
            printer_id = data.get('printer_id')
            template_id = data.get('template_id')
        else:
            bin_ids = request.POST.getlist('bin_ids[]') or request.POST.getlist('bin_ids')
            printer_id = request.POST.get('printer_id')
            template_id = request.POST.get('template_id')

        # Validações
        if not bin_ids:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum contentor selecionado.'
            }, status=400)

        if not printer_id or not template_id:
            return JsonResponse({
                'success': False,
                'message': 'Impressora e template são obrigatórios.'
            }, status=400)

        # Executar impressão
        print_status = _print_bin_labels(bin_ids, printer_id, template_id, request.user)

        if print_status['success']:
            return JsonResponse({
                'success': True,
                'message': f'{print_status["printed"]} etiqueta(s) enviada(s) para impressão.',
                'printed': print_status['printed'],
                'errors': print_status['errors']
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao imprimir etiquetas.',
                'printed': print_status['printed'],
                'errors': print_status['errors']
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dados JSON inválidos.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao imprimir: {str(e)}'
        }, status=500)


def _print_bin_labels(bin_ids, printer_id, template_id, user):
    """
    Função auxiliar para imprimir etiquetas de múltiplos contentores.
    Retorna dict com status da impressão.
    """
    from apps.labels.models import LabelTemplate, PrinterConfiguration, PrintJob
    from apps.labels.epl_generator import EPLGenerator
    from apps.labels.printer_client import PrinterClient

    result = {
        'success': True,
        'printed': 0,
        'errors': []
    }

    try:
        template = LabelTemplate.objects.get(id=template_id, is_active=True)
        printer = PrinterConfiguration.objects.get(id=printer_id, is_active=True)
        client = PrinterClient(printer)

        for bin_id in bin_ids:
            try:
                bin_obj = Bin.objects.get(id=bin_id, is_active=True)

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
                    created_by=user,
                    updated_by=user
                )
                print_job.save()

                # Enviar para impressora
                success, error_message = client.send_epl(epl_content)

                if success:
                    print_job.status = 'SUCCESS'
                    print_job.printed_at = timezone.now()
                    result['printed'] += 1
                else:
                    print_job.status = 'FAILED'
                    print_job.error_message = error_message
                    result['errors'].append({
                        'bin_id': str(bin_id),
                        'bin_code': bin_obj.code,
                        'error': error_message
                    })

                print_job.save()

            except Bin.DoesNotExist:
                result['errors'].append({
                    'bin_id': str(bin_id),
                    'error': 'Contentor não encontrado'
                })
            except Exception as e:
                result['errors'].append({
                    'bin_id': str(bin_id),
                    'error': str(e)
                })

    except LabelTemplate.DoesNotExist:
        result['success'] = False
        result['errors'].append({'error': 'Template não encontrado'})
    except PrinterConfiguration.DoesNotExist:
        result['success'] = False
        result['errors'].append({'error': 'Impressora não encontrada'})
    except Exception as e:
        result['success'] = False
        result['errors'].append({'error': str(e)})

    # Se houve erros mas algumas impressões funcionaram, ainda consideramos sucesso parcial
    if result['errors'] and result['printed'] > 0:
        result['success'] = True  # Sucesso parcial

    return result
