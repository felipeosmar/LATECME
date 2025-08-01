#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.materials.models import Material, Supplier, MaterialSupplier, MaterialCategory
from decimal import Decimal

def create_categories():
    """Criar categorias de materiais"""
    categories_data = [
        {'name': 'Ligas de Alumínio', 'description': 'Ligas baseadas em alumínio', 'color': '#007bff'},
        {'name': 'Ligas de Titânio', 'description': 'Ligas baseadas em titânio', 'color': '#6c757d'},
        {'name': 'Aços Inoxidáveis', 'description': 'Aços resistentes à corrosão', 'color': '#28a745'},
        {'name': 'Superligas', 'description': 'Ligas de alta performance', 'color': '#dc3545'},
        {'name': 'Ligas de Cobre', 'description': 'Ligas baseadas em cobre', 'color': '#fd7e14'},
    ]
    
    for cat_data in categories_data:
        category, created = MaterialCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
                'color': cat_data['color']
            }
        )
        if created:
            print(f"✓ Categoria criada: {category.name}")
        else:
            print(f"- Categoria já existe: {category.name}")

def create_suppliers():
    """Criar fornecedores de exemplo"""
    suppliers_data = [
        {
            'code': 'ALU001',
            'name': 'Alcoa Brasil',
            'cnpj': '01.234.567/0001-00',
            'contact_email': 'vendas@alcoa.com.br',
            'contact_phone': '(11) 3456-7890',
            'address': 'São Paulo, SP'
        },
        {
            'code': 'TIT001',
            'name': 'Titanium Industries',
            'cnpj': '02.345.678/0001-11',
            'contact_email': 'sales@titanium.com',
            'contact_phone': '(21) 2345-6789',
            'address': 'Rio de Janeiro, RJ'
        },
        {
            'code': 'MET001',
            'name': 'MetalTech Solutions',
            'cnpj': '03.456.789/0001-22',
            'contact_email': 'comercial@metaltech.com.br',
            'contact_phone': '(31) 3456-7890',
            'address': 'Belo Horizonte, MG'
        }
    ]
    
    for sup_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            code=sup_data['code'],
            defaults=sup_data
        )
        if created:
            print(f"✓ Fornecedor criado: {supplier.name}")
        else:
            print(f"- Fornecedor já existe: {supplier.name}")

def create_materials():
    """Criar materiais de exemplo"""
    
    # Buscar categorias
    al_category = MaterialCategory.objects.get(name='Ligas de Alumínio')
    ti_category = MaterialCategory.objects.get(name='Ligas de Titânio')
    ss_category = MaterialCategory.objects.get(name='Aços Inoxidáveis')
    
    materials_data = [
        {
            'code': 'AL7075',
            'name': 'Alumínio 7075-T6',
            'material_type': 'AL',
            'category': al_category,
            'density': Decimal('2.810'),
            'melting_point': Decimal('635.0'),
            # 'composition': {
            #     'Al': 90.0,
            #     'Zn': 5.6,
            #     'Mg': 2.5,
            #     'Cu': 1.6,
            #     'Cr': 0.23
            # },
            'specifications': {
                'resistencia_tracao': '572 MPa',
                'limite_escoamento': '503 MPa',
                'alongamento': '11%',
                'dureza': '150 HB'
            },
            'storage_requirements': 'Ambiente seco, temperatura controlada',
            'safety_notes': 'Usar EPIs adequados durante manuseio'
        },
        {
            'code': 'TI6AL4V',
            'name': 'Titânio Grade 5 (Ti-6Al-4V)',
            'material_type': 'TI',
            'category': ti_category,
            'density': Decimal('4.430'),
            'melting_point': Decimal('1660.0'),
            # 'composition': {
            #     'Ti': 89.0,
            #     'Al': 6.0,
            #     'V': 4.0,
            #     'Fe': 0.25,
            #     'O': 0.2
            # },
            'specifications': {
                'resistencia_tracao': '1170 MPa',
                'limite_escoamento': '1100 MPa',
                'alongamento': '14%',
                'modulo_elastico': '114 GPa'
            },
            'storage_requirements': 'Ambiente inerte, evitar contaminação',
            'safety_notes': 'Material inflamável em pó, manter longe de fontes de ignição'
        },
        {
            'code': 'SS316L',
            'name': 'Aço Inoxidável 316L',
            'material_type': 'SS',
            'category': ss_category,
            'density': Decimal('8.000'),
            'melting_point': Decimal('1400.0'),
            # 'composition': {
            #     'Fe': 65.0,
            #     'Cr': 17.0,
            #     'Ni': 12.0,
            #     'Mo': 2.5,
            #     'Mn': 2.0,
            #     'Si': 1.0,
            #     'C': 0.03
            # },
            'specifications': {
                'resistencia_tracao': '620 MPa',
                'limite_escoamento': '310 MPa',
                'alongamento': '30%',
                'dureza': '217 HB'
            },
            'storage_requirements': 'Local seco, evitar contaminação',
            'safety_notes': 'Cuidado com partículas durante processamento'
        },
        {
            'code': 'IN718',
            'name': 'Inconel 718',
            'material_type': 'IN',
            'category': ss_category,  # Usando categoria de aço por enquanto
            'density': Decimal('8.220'),
            'melting_point': Decimal('1336.0'),
            # 'composition': {
            #     'Ni': 52.5,
            #     'Cr': 19.0,
            #     'Fe': 18.5,
            #     'Nb': 5.1,
            #     'Mo': 3.0,
            #     'Ti': 0.9,
            #     'Al': 0.5
            # },
            'specifications': {
                'resistencia_tracao': '1275 MPa',
                'limite_escoamento': '1034 MPa',
                'alongamento': '12%',
                'temperatura_servico': '650°C'
            },
            'storage_requirements': 'Ambiente controlado, baixa umidade',
            'safety_notes': 'Superliga de alta temperatura, cuidados especiais no manuseio'
        }
    ]
    
    for mat_data in materials_data:
        material, created = Material.objects.get_or_create(
            code=mat_data['code'],
            defaults=mat_data
        )
        if created:
            print(f"✓ Material criado: {material.code} - {material.name}")
        else:
            print(f"- Material já existe: {material.code}")

def create_material_suppliers():
    """Criar relações material-fornecedor"""
    
    # Buscar materiais e fornecedores
    try:
        al7075 = Material.objects.get(code='AL7075')
        ti6al4v = Material.objects.get(code='TI6AL4V')
        ss316l = Material.objects.get(code='SS316L')
        in718 = Material.objects.get(code='IN718')
        
        alcoa = Supplier.objects.get(code='ALU001')
        titanium = Supplier.objects.get(code='TIT001')
        metaltech = Supplier.objects.get(code='MET001')
        
        # Relações material-fornecedor
        relations_data = [
            # AL7075
            {
                'material': al7075,
                'supplier': alcoa,
                'supplier_code': 'ALC-7075-T6',
                'price_per_kg': Decimal('85.50'),
                'minimum_order': Decimal('25.0'),
                'lead_time_days': 15
            },
            {
                'material': al7075,
                'supplier': metaltech,
                'supplier_code': 'MT-AL7075',
                'price_per_kg': Decimal('89.90'),
                'minimum_order': Decimal('50.0'),
                'lead_time_days': 10
            },
            
            # TI6AL4V
            {
                'material': ti6al4v,
                'supplier': titanium,
                'supplier_code': 'TI-6-4-GRADE5',
                'price_per_kg': Decimal('450.00'),
                'minimum_order': Decimal('10.0'),
                'lead_time_days': 30
            },
            {
                'material': ti6al4v,
                'supplier': metaltech,
                'supplier_code': 'MT-TI64',
                'price_per_kg': Decimal('485.00'),
                'minimum_order': Decimal('5.0'),
                'lead_time_days': 25
            },
            
            # SS316L
            {
                'material': ss316l,
                'supplier': metaltech,
                'supplier_code': 'MT-316L',
                'price_per_kg': Decimal('125.00'),
                'minimum_order': Decimal('20.0'),
                'lead_time_days': 12
            },
            
            # IN718
            {
                'material': in718,
                'supplier': titanium,
                'supplier_code': 'TI-IN718',
                'price_per_kg': Decimal('850.00'),
                'minimum_order': Decimal('5.0'),
                'lead_time_days': 45
            }
        ]
        
        for rel_data in relations_data:
            mat_sup, created = MaterialSupplier.objects.get_or_create(
                material=rel_data['material'],
                supplier=rel_data['supplier'],
                defaults={
                    'supplier_code': rel_data['supplier_code'],
                    'price_per_kg': rel_data['price_per_kg'],
                    'minimum_order': rel_data['minimum_order'],
                    'lead_time_days': rel_data['lead_time_days']
                }
            )
            if created:
                print(f"✓ Relação criada: {mat_sup.material.code} - {mat_sup.supplier.name}")
            else:
                print(f"- Relação já existe: {mat_sup.material.code} - {mat_sup.supplier.name}")
    
    except Exception as e:
        print(f"Erro ao criar relações: {e}")

if __name__ == '__main__':
    print("Criando dados de exemplo para materiais...")
    create_categories()
    create_suppliers()
    create_materials()
    create_material_suppliers()
    print("Dados de materiais criados com sucesso!")