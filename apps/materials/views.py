from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Min, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from datetime import datetime
from .models import Material, Supplier, MaterialSupplier, MaterialCategory, MaterialComposition
from .forms import MaterialForm, SupplierForm, MaterialCompositionFormSet


@login_required
def material_list(request):
    """Lista de materiais com filtros e busca"""
    materials = Material.objects.filter(is_active=True).select_related('category').prefetch_related('suppliers')
    
    # Filtros
    search = request.GET.get('search', '')
    material_type = request.GET.get('type', '')
    category_id = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if search:
        materials = materials.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search)
        )

    if material_type:
        materials = materials.filter(material_type=material_type)

    if category_id:
        materials = materials.filter(category_id=category_id)

    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            materials = materials.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            materials = materials.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass
    
    # Paginação
    paginator = Paginator(materials, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    categories = MaterialCategory.objects.filter(is_active=True)
    material_types = Material.MATERIAL_TYPES
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'material_type': material_type,
        'category_id': int(category_id) if category_id else '',
        'categories': categories,
        'material_types': material_types,
<<<<<<< HEAD
        'total_materials': materials.count(),
        'date_from': date_from,
        'date_to': date_to,
=======
        'total_materials': paginator.count,
>>>>>>> 1dc4d9c0fa33a126346b34bb4c100b9362961f74
    }
    
    return render(request, 'materials/material_list.html', context)


@login_required
def material_detail(request, material_id):
    """Detalhes de um material específico"""
    material = get_object_or_404(
        Material.objects.select_related('category').prefetch_related(
            'materialsupplier_set__supplier'
        ), 
        id=material_id, 
        is_active=True
    )
    
    # Fornecedores do material
    suppliers = material.materialsupplier_set.filter(
        supplier__is_active=True
    ).order_by('price_per_kg')
    
    context = {
        'material': material,
        'suppliers': suppliers,
    }
    
    return render(request, 'materials/material_detail.html', context)


@login_required
def material_create(request):
    """Criar novo material"""
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        formset = MaterialCompositionFormSet(request.POST, prefix='compositions')
        
        if form.is_valid() and formset.is_valid():
            material = form.save(commit=False)
            material.created_by = request.user
            material.updated_by = request.user
            material.save()
            
            # Salvar composições
            formset.instance = material
            formset.save()
            
            messages.success(request, f'Material {material.code} criado com sucesso!')
            return redirect('materials:detail', material_id=material.id)
    else:
        form = MaterialForm()
        formset = MaterialCompositionFormSet(prefix='compositions')
    
    return render(request, 'materials/material_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Novo Material',
        'action': 'Criar'
    })


@login_required
def material_edit(request, material_id):
    """Editar material existente"""
    material = get_object_or_404(Material, id=material_id, is_active=True)
    
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        formset = MaterialCompositionFormSet(request.POST, instance=material, prefix='compositions')
        
        if form.is_valid() and formset.is_valid():
            material = form.save(commit=False)
            material.updated_by = request.user
            material.save()
            
            # Salvar composições
            formset.save()
            
            messages.success(request, f'Material {material.code} atualizado com sucesso!')
            return redirect('materials:detail', material_id=material.id)
    else:
        form = MaterialForm(instance=material)
        formset = MaterialCompositionFormSet(instance=material, prefix='compositions')
    
    return render(request, 'materials/material_form.html', {
        'form': form,
        'formset': formset,
        'material': material,
        'title': f'Editar Material {material.code}',
        'action': 'Salvar'
    })


@login_required
def supplier_list(request):
    """Lista de fornecedores"""
    suppliers = Supplier.objects.filter(is_active=True).annotate(
        material_count=Count('materials')
    )

    # Filtros
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(cnpj__icontains=search)
        )

    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            suppliers = suppliers.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            suppliers = suppliers.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            pass

    # Paginação
    paginator = Paginator(suppliers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
<<<<<<< HEAD
        'total_suppliers': suppliers.count(),
        'date_from': date_from,
        'date_to': date_to,
=======
        'total_suppliers': paginator.count,
>>>>>>> 1dc4d9c0fa33a126346b34bb4c100b9362961f74
    }

    return render(request, 'materials/supplier_list.html', context)


@login_required
def supplier_detail(request, supplier_id):
    """Detalhes de um fornecedor"""
    supplier = get_object_or_404(
        Supplier.objects.prefetch_related(
            'materialsupplier_set__material'
        ), 
        id=supplier_id, 
        is_active=True
    )
    
    # Materiais do fornecedor
    materials = supplier.materialsupplier_set.filter(
        material__is_active=True
    ).select_related('material').order_by('material__code')
    
    context = {
        'supplier': supplier,
        'materials': materials,
    }
    
    return render(request, 'materials/supplier_detail.html', context)


@login_required
def supplier_create(request):
    """Criar novo fornecedor"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.updated_by = request.user
            supplier.save()
            messages.success(request, f'Fornecedor {supplier.name} criado com sucesso!')
            return redirect('materials:supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierForm()
    
    return render(request, 'materials/supplier_form.html', {
        'form': form,
        'title': 'Novo Fornecedor',
        'action': 'Criar'
    })


@login_required
def supplier_edit(request, supplier_id):
    """Editar fornecedor"""
    supplier = get_object_or_404(Supplier, id=supplier_id, is_active=True)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.updated_by = request.user
            supplier.save()
            messages.success(request, f'Fornecedor {supplier.name} atualizado com sucesso!')
            return redirect('materials:supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'materials/supplier_form.html', {
        'form': form,
        'supplier': supplier,
        'title': 'Editar Fornecedor',
        'action': 'Salvar'
    })


@login_required
def dashboard_materials(request):
    """Dashboard do módulo de materiais"""
    # Estatísticas
    total_materials = Material.objects.filter(is_active=True).count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    total_categories = MaterialCategory.objects.filter(is_active=True).count()
    
    # Materiais por tipo
    materials_by_type = Material.objects.filter(is_active=True).values(
        'material_type'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Fornecedores com mais materiais
    top_suppliers = Supplier.objects.filter(is_active=True).annotate(
        material_count=Count('materials')
    ).order_by('-material_count')[:5]
    
    # Materiais sem fornecedores
    materials_no_suppliers = Material.objects.filter(
        is_active=True,
        suppliers__isnull=True
    ).count()
    
    context = {
        'total_materials': total_materials,
        'total_suppliers': total_suppliers,
        'total_categories': total_categories,
        'materials_by_type': materials_by_type,
        'top_suppliers': top_suppliers,
        'materials_no_suppliers': materials_no_suppliers,
    }
    
    return render(request, 'materials/dashboard.html', context)


@login_required
def material_search_api(request):
    """API para busca de materiais (AJAX)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})

    materials = Material.objects.filter(
        Q(code__icontains=query) | Q(name__icontains=query),
        is_active=True
    )[:10]

    results = []
    for material in materials:
        results.append({
            'id': material.id,
            'code': material.code,
            'name': material.name,
            'type': material.get_material_type_display(),
            'best_price': float(material.get_best_price()) if material.get_best_price() else None
        })

    return JsonResponse({'results': results})


@login_required
def supplier_search_api(request):
    """API para busca de fornecedores (AJAX)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})

    suppliers = Supplier.objects.filter(
        Q(name__icontains=query) | Q(code__icontains=query) | Q(cnpj__icontains=query),
        is_active=True
    ).annotate(material_count=Count('materials'))[:10]

    results = []
    for supplier in suppliers:
        results.append({
            'id': supplier.id,
            'code': supplier.code,
            'name': supplier.name,
            'cnpj': supplier.cnpj,
            'material_count': supplier.material_count
        })

    return JsonResponse({'results': results})