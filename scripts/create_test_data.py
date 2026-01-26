#!/usr/bin/env python
"""
Script para criar dados de teste para o sistema LATECME.
Gera dados para todas as funcionalidades com quantidade suficiente para testar paginação.
"""

import os
import sys

# Adiciona o diretório raiz do projeto ao path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import django
import random
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.models import UserRole
from apps.materials.models import Material, Supplier, MaterialSupplier
from apps.inventory.models import (
    Warehouse, MaterialStock, StockMovement, StockReservation,
    InventoryCount, InventoryCountItem, ProductionOrder, Bin, BinHistory, Batch, BatchItem
)

User = get_user_model()


def create_users():
    """Criar usuários de teste"""
    print("Criando usuários...")

    # Criar roles
    roles_data = [
        {'name': 'Administrador', 'description': 'Acesso total ao sistema'},
        {'name': 'Gerente de Produção', 'description': 'Gerencia ordens de produção e bateladas'},
        {'name': 'Operador de Estoque', 'description': 'Gerencia movimentações de estoque'},
        {'name': 'Técnico de Qualidade', 'description': 'Controle de qualidade e certificados'},
        {'name': 'Visualizador', 'description': 'Apenas visualização de dados'},
    ]

    roles = {}
    for role_data in roles_data:
        role, _ = UserRole.objects.get_or_create(
            name=role_data['name'],
            defaults={'description': role_data['description']}
        )
        roles[role_data['name']] = role

    # Criar usuários
    users_data = [
        {'username': 'admin', 'email': 'admin@latecme.com', 'first_name': 'Admin', 'last_name': 'Sistema', 'role': 'Administrador', 'is_superuser': True, 'is_staff': True},
        {'username': 'gerente.prod', 'email': 'gerente.prod@latecme.com', 'first_name': 'Carlos', 'last_name': 'Silva', 'role': 'Gerente de Produção'},
        {'username': 'operador1', 'email': 'operador1@latecme.com', 'first_name': 'Maria', 'last_name': 'Santos', 'role': 'Operador de Estoque'},
        {'username': 'operador2', 'email': 'operador2@latecme.com', 'first_name': 'João', 'last_name': 'Oliveira', 'role': 'Operador de Estoque'},
        {'username': 'operador3', 'email': 'operador3@latecme.com', 'first_name': 'Ana', 'last_name': 'Costa', 'role': 'Operador de Estoque'},
        {'username': 'qualidade1', 'email': 'qualidade1@latecme.com', 'first_name': 'Pedro', 'last_name': 'Ferreira', 'role': 'Técnico de Qualidade'},
        {'username': 'qualidade2', 'email': 'qualidade2@latecme.com', 'first_name': 'Lucia', 'last_name': 'Almeida', 'role': 'Técnico de Qualidade'},
        {'username': 'viewer1', 'email': 'viewer1@latecme.com', 'first_name': 'Roberto', 'last_name': 'Lima', 'role': 'Visualizador'},
    ]

    users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'role': roles.get(user_data['role']),
                'status': 'approved',
                'is_superuser': user_data.get('is_superuser', False),
                'is_staff': user_data.get('is_staff', False),
            }
        )
        if created:
            user.set_password('teste123')
            user.save()
        users.append(user)

    print(f"  {len(users)} usuários criados/verificados")
    return users


def create_suppliers():
    """Criar fornecedores"""
    print("Criando fornecedores...")

    suppliers_data = [
        {'code': 'SAND001', 'name': 'Sandvik Additive Manufacturing', 'cnpj': '12345678000101', 'address': 'Sandviken, Suécia'},
        {'code': 'CARP001', 'name': 'Carpenter Technology', 'cnpj': '23456789000102', 'address': 'Philadelphia, EUA'},
        {'code': 'GKN001', 'name': 'GKN Powder Metallurgy', 'cnpj': '34567890000103', 'address': 'Redditch, Reino Unido'},
        {'code': 'HOGA001', 'name': 'Höganäs AB', 'cnpj': '45678901000104', 'address': 'Höganäs, Suécia'},
        {'code': 'PRAX001', 'name': 'Praxair Surface Technologies', 'cnpj': '56789012000105', 'address': 'Indianapolis, EUA'},
        {'code': 'TEKN001', 'name': 'Tekna Plasma Systems', 'cnpj': '67890123000106', 'address': 'Sherbrooke, Canadá'},
        {'code': 'AMES001', 'name': 'AMES Group', 'cnpj': '78901234000107', 'address': 'Barcelona, Espanha'},
        {'code': 'ERAC001', 'name': 'Erasteel', 'cnpj': '89012345000108', 'address': 'Paris, França'},
        {'code': 'LIND001', 'name': 'Linde Advanced Material', 'cnpj': '90123456000109', 'address': 'Munique, Alemanha'},
        {'code': 'OERLI001', 'name': 'Oerlikon Metco', 'cnpj': '01234567000110', 'address': 'Wohlen, Suíça'},
        {'code': 'APAM001', 'name': 'AP&C Advanced Powders', 'cnpj': '11234567000111', 'address': 'Boisbriand, Canadá'},
        {'code': 'LPW001', 'name': 'LPW Technology', 'cnpj': '21234567000112', 'address': 'Widnes, Reino Unido'},
    ]

    suppliers = []
    for sup_data in suppliers_data:
        supplier, _ = Supplier.objects.get_or_create(
            code=sup_data['code'],
            defaults={
                'name': sup_data['name'],
                'cnpj': sup_data['cnpj'],
                'address': sup_data['address'],
                'contact_email': f"comercial@{sup_data['code'].lower().replace('001', '')}.com",
                'contact_phone': f"+{random.randint(1,99)} {random.randint(100,999)} {random.randint(1000000,9999999)}",
                'is_active': True,
            }
        )
        suppliers.append(supplier)

    print(f"  {len(suppliers)} fornecedores criados/verificados")
    return suppliers


def create_materials(suppliers, users):
    """Criar materiais"""
    print("Criando materiais...")

    materials_data = [
        # Ligas de Alumínio
        {'code': 'AL7075', 'name': 'Alumínio 7075', 'type': 'AL', 'density': 2.81},
        {'code': 'AL6061', 'name': 'Alumínio 6061', 'type': 'AL', 'density': 2.70},
        {'code': 'ALSI10MG', 'name': 'AlSi10Mg', 'type': 'AL', 'density': 2.67},
        {'code': 'ALSI7MG', 'name': 'AlSi7Mg', 'type': 'AL', 'density': 2.68},
        {'code': 'AL2024', 'name': 'Alumínio 2024', 'type': 'AL', 'density': 2.78},

        # Ligas de Titânio
        {'code': 'TI6AL4V', 'name': 'Titânio Ti6Al4V', 'type': 'TI', 'density': 4.43},
        {'code': 'TI6AL4VELI', 'name': 'Titânio Ti6Al4V ELI', 'type': 'TI', 'density': 4.43},
        {'code': 'TIGR5', 'name': 'Titânio Grau 5', 'type': 'TI', 'density': 4.42},
        {'code': 'TIGR23', 'name': 'Titânio Grau 23', 'type': 'TI', 'density': 4.43},
        {'code': 'CPTI', 'name': 'Titânio CP (Puro)', 'type': 'TI', 'density': 4.51},

        # Aços Inoxidáveis
        {'code': 'SS316L', 'name': 'Aço Inox 316L', 'type': 'SS', 'density': 7.99},
        {'code': 'SS304L', 'name': 'Aço Inox 304L', 'type': 'SS', 'density': 7.93},
        {'code': 'SS174PH', 'name': 'Aço Inox 17-4 PH', 'type': 'SS', 'density': 7.78},
        {'code': 'SS155PH', 'name': 'Aço Inox 15-5 PH', 'type': 'SS', 'density': 7.78},
        {'code': 'MS1STEEL', 'name': 'Maraging Steel MS1', 'type': 'SS', 'density': 8.10},

        # Ligas de Níquel (usando IN para Inconel)
        {'code': 'IN718', 'name': 'Inconel 718', 'type': 'IN', 'density': 8.19},
        {'code': 'IN625', 'name': 'Inconel 625', 'type': 'IN', 'density': 8.44},
        {'code': 'IN939', 'name': 'Inconel 939', 'type': 'IN', 'density': 8.25},
        {'code': 'HASTX', 'name': 'Hastelloy X', 'type': 'NI', 'density': 8.22},
        {'code': 'WASPALOY', 'name': 'Waspaloy', 'type': 'NI', 'density': 8.19},

        # Ligas de Cobalto
        {'code': 'COCRMO', 'name': 'CoCrMo (Cobalto-Cromo)', 'type': 'CO', 'density': 8.30},
        {'code': 'COCRF75', 'name': 'CoCrF75', 'type': 'CO', 'density': 8.28},
        {'code': 'STELLITE6', 'name': 'Stellite 6', 'type': 'CO', 'density': 8.44},

        # Cobre e Ligas
        {'code': 'CUCRZ', 'name': 'CuCrZr', 'type': 'CU', 'density': 8.89},
        {'code': 'CUPURE', 'name': 'Cobre Puro', 'type': 'CU', 'density': 8.96},
        {'code': 'CUBRONZE', 'name': 'Bronze (CuSn10)', 'type': 'CU', 'density': 8.78},

        # Outros materiais
        {'code': 'WPURE', 'name': 'Tungstênio Puro', 'type': 'OTHER', 'density': 19.25},
        {'code': 'TAPURE', 'name': 'Tântalo Puro', 'type': 'OTHER', 'density': 16.69},
        {'code': 'MOPURE', 'name': 'Molibdênio Puro', 'type': 'OTHER', 'density': 10.28},
    ]

    materials = []
    admin_user = users[0]

    for mat_data in materials_data:
        material, created = Material.objects.get_or_create(
            code=mat_data['code'],
            defaults={
                'name': mat_data['name'],
                'material_type': mat_data['type'],
                'density': Decimal(str(mat_data['density'])),
                'storage_requirements': f"Armazenar em local seco e controlado",
                'is_active': True,
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )
        materials.append(material)

        # Criar relações com fornecedores (2-4 fornecedores por material)
        if created:
            selected_suppliers = random.sample(suppliers, random.randint(2, 4))
            for supplier in selected_suppliers:
                MaterialSupplier.objects.get_or_create(
                    material=material,
                    supplier=supplier,
                    defaults={
                        'supplier_code': f"{supplier.code}-{mat_data['code']}",
                        'price_per_kg': Decimal(str(random.uniform(50, 500))).quantize(Decimal('0.01')),
                        'lead_time_days': random.randint(7, 60),
                        'minimum_order': Decimal(str(random.randint(5, 50))),
                        'available': random.random() > 0.2,
                    }
                )

    print(f"  {len(materials)} materiais criados/verificados")
    return materials


def create_warehouses(users):
    """Criar armazéns"""
    print("Criando armazéns...")

    warehouses_data = [
        {'code': 'ARM-01', 'name': 'Armazém Principal', 'location': 'Galpão A - Setor 1'},
        {'code': 'ARM-02', 'name': 'Armazém de Matéria-Prima', 'location': 'Galpão A - Setor 2'},
        {'code': 'ARM-03', 'name': 'Armazém de Produção', 'location': 'Galpão B - Área de Produção'},
        {'code': 'ARM-04', 'name': 'Armazém Climatizado', 'location': 'Galpão C - Sala Climatizada'},
        {'code': 'ARM-05', 'name': 'Armazém de Quarentena', 'location': 'Galpão D - Área de Inspeção'},
        {'code': 'ARM-06', 'name': 'Armazém de Expedição', 'location': 'Galpão E - Doca de Expedição'},
    ]

    warehouses = []
    admin_user = users[0]
    managers = [u for u in users if 'gerente' in u.username or 'operador' in u.username]

    for wh_data in warehouses_data:
        warehouse, _ = Warehouse.objects.get_or_create(
            code=wh_data['code'],
            defaults={
                'name': wh_data['name'],
                'location': wh_data['location'],
                'description': f"Armazém para estocagem de materiais - {wh_data['name']}",
                'manager': random.choice(managers) if managers else admin_user,
                'is_active': True,
                'created_by': admin_user,
                'updated_by': admin_user,
            }
        )
        warehouses.append(warehouse)

    print(f"  {len(warehouses)} armazéns criados/verificados")
    return warehouses


def create_material_stocks(materials, warehouses, users):
    """Criar estoques de materiais"""
    print("Criando estoques de materiais...")

    stocks = []
    admin_user = users[0]

    # Cada material em 1-3 armazéns
    for material in materials:
        num_warehouses = random.randint(1, 3)
        selected_warehouses = random.sample(warehouses, num_warehouses)

        for warehouse in selected_warehouses:
            stock, created = MaterialStock.objects.get_or_create(
                material=material,
                warehouse=warehouse,
                defaults={
                    'current_quantity': Decimal(str(random.uniform(10, 500))).quantize(Decimal('0.001')),
                    'reserved_quantity': Decimal('0'),
                    'minimum_stock': Decimal(str(random.uniform(5, 50))).quantize(Decimal('0.001')),
                    'maximum_stock': Decimal(str(random.uniform(500, 1000))).quantize(Decimal('0.001')),
                    'location_code': f"P{random.randint(1,10)}-E{random.randint(1,5)}-N{random.randint(1,3)}",
                    'last_movement_date': timezone.now() - timedelta(days=random.randint(0, 30)),
                }
            )
            stocks.append(stock)

    print(f"  {len(stocks)} estoques criados/verificados")
    return stocks


def create_stock_movements(materials, warehouses, users):
    """Criar movimentações de estoque"""
    print("Criando movimentações de estoque...")

    movements = []
    operators = [u for u in users if 'operador' in u.username]
    if not operators:
        operators = users

    movement_types = ['IN', 'OUT', 'ADJUSTMENT', 'TRANSFER']
    reasons = {
        'IN': ['PURCHASE', 'RETURN', 'INVENTORY_ADJUSTMENT'],
        'OUT': ['PRODUCTION', 'SALE', 'INTERNAL_USE', 'LOSS'],
        'ADJUSTMENT': ['INVENTORY_ADJUSTMENT'],
        'TRANSFER': ['TRANSFER'],
    }

    # Criar 150 movimentações nos últimos 90 dias
    for i in range(150):
        material = random.choice(materials)
        warehouse = random.choice(warehouses)
        movement_type = random.choice(movement_types)
        reason = random.choice(reasons[movement_type])

        days_ago = random.randint(0, 90)
        movement_date = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

        movement = StockMovement.objects.create(
            material=material,
            warehouse=warehouse,
            movement_type=movement_type,
            reason=reason,
            quantity=Decimal(str(random.uniform(1, 100))).quantize(Decimal('0.001')),
            unit_cost=Decimal(str(random.uniform(50, 300))).quantize(Decimal('0.01')) if movement_type == 'IN' else None,
            batch_number=f"LOTE-{random.randint(2023, 2024)}-{random.randint(1000, 9999)}" if random.random() > 0.3 else '',
            reference_document=f"DOC-{random.randint(10000, 99999)}" if random.random() > 0.5 else '',
            user=random.choice(operators),
            notes=f"Movimentação de teste #{i+1}" if random.random() > 0.7 else '',
            created_by=random.choice(operators),
            updated_by=random.choice(operators),
        )
        movement.created_at = movement_date
        movement.save(update_fields=['created_at'])
        movements.append(movement)

    print(f"  {len(movements)} movimentações criadas")
    return movements


def create_stock_reservations(materials, warehouses, users):
    """Criar reservas de estoque"""
    print("Criando reservas de estoque...")

    reservations = []
    operators = [u for u in users if 'operador' in u.username or 'gerente' in u.username]
    if not operators:
        operators = users

    purposes = [
        'Ordem de Produção',
        'Pedido de Cliente',
        'Teste de Qualidade',
        'Amostra para Cliente',
        'Manutenção Preventiva',
    ]

    # Criar 30 reservas
    for i in range(30):
        material = random.choice(materials)
        warehouse = random.choice(warehouses)
        user = random.choice(operators)

        days_ahead = random.randint(1, 30)
        expiry_date = timezone.now() + timedelta(days=days_ahead)

        reservation = StockReservation.objects.create(
            material=material,
            warehouse=warehouse,
            quantity=Decimal(str(random.uniform(5, 50))).quantize(Decimal('0.001')),
            reserved_by=user,
            purpose=random.choice(purposes),
            expiry_date=expiry_date,
            reference_document=f"RES-{random.randint(10000, 99999)}",
            notes=f"Reserva de teste #{i+1}" if random.random() > 0.5 else '',
        )
        reservations.append(reservation)

    print(f"  {len(reservations)} reservas criadas")
    return reservations


def create_bins(warehouses, materials, users):
    """Criar contentores (bins)"""
    print("Criando contentores...")

    bins = []
    admin_user = users[0]
    operators = [u for u in users if 'operador' in u.username]
    if not operators:
        operators = users

    bin_statuses = ['EMPTY', 'LOADED', 'LOADED', 'LOADED', 'IN_USE', 'MAINTENANCE']  # Mais LOADED

    # Criar 80 contentores distribuídos pelos armazéns
    bin_counter = 1
    for warehouse in warehouses:
        num_bins = random.randint(10, 20)
        for _ in range(num_bins):
            status = random.choice(bin_statuses)

            # Se carregado ou em uso, definir material
            current_material = None
            current_quantity = Decimal('0')
            current_supplier_batch = ''
            current_certificate = ''

            if status in ['LOADED', 'IN_USE']:
                current_material = random.choice(materials)
                current_quantity = Decimal(str(random.uniform(10, 80))).quantize(Decimal('0.001'))
                current_supplier_batch = f"LOTE-{random.randint(2023, 2024)}-{random.randint(1000, 9999)}"
                current_certificate = f"CERT-{random.randint(10000, 99999)}" if random.random() > 0.3 else ''

            bin_obj = Bin.objects.create(
                code=f"BIN-{bin_counter:04d}",
                warehouse=warehouse,
                status=status,
                capacity=Decimal(str(random.choice([50, 100, 150, 200]))),
                current_material=current_material,
                current_quantity=current_quantity,
                current_supplier_batch=current_supplier_batch,
                current_certificate=current_certificate,
                location_code=f"L{random.randint(1,5)}-R{random.randint(1,10)}-P{random.randint(1,4)}",
                notes=f"Contentor #{bin_counter}" if random.random() > 0.7 else '',
                is_active=True,
                created_by=admin_user,
                updated_by=admin_user,
            )
            bins.append(bin_obj)
            bin_counter += 1

    print(f"  {len(bins)} contentores criados")
    return bins


def create_bin_history(bins, materials, users):
    """Criar histórico de contentores"""
    print("Criando histórico de contentores...")

    history_entries = []
    operators = [u for u in users if 'operador' in u.username]
    if not operators:
        operators = users

    movement_types = ['IN', 'OUT', 'EMPTY', 'ADJUSTMENT']

    # Criar histórico para cada bin carregado ou em uso
    for bin_obj in bins:
        if bin_obj.status in ['LOADED', 'IN_USE', 'EMPTY']:
            # Criar 2-8 entradas de histórico por bin
            num_entries = random.randint(2, 8)
            quantity_before = Decimal('0')

            for i in range(num_entries):
                movement_type = random.choice(movement_types)
                material = bin_obj.current_material or random.choice(materials)
                quantity = Decimal(str(random.uniform(5, 30))).quantize(Decimal('0.001'))

                if movement_type == 'IN':
                    quantity_after = quantity_before + quantity
                elif movement_type in ['OUT', 'EMPTY']:
                    quantity = min(quantity, quantity_before) if quantity_before > 0 else Decimal('0.001')
                    quantity_after = quantity_before - quantity
                else:
                    quantity_after = quantity_before + (quantity if random.random() > 0.5 else -quantity)
                    quantity_after = max(quantity_after, Decimal('0'))

                days_ago = random.randint(1, 60)
                entry_date = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

                history = BinHistory.objects.create(
                    bin=bin_obj,
                    movement_type=movement_type,
                    material=material,
                    quantity=quantity,
                    quantity_before=quantity_before,
                    quantity_after=quantity_after,
                    supplier_batch=f"LOTE-{random.randint(2023, 2024)}-{random.randint(1000, 9999)}" if movement_type == 'IN' else '',
                    certificate=f"CERT-{random.randint(10000, 99999)}" if movement_type == 'IN' and random.random() > 0.5 else '',
                    performed_by=random.choice(operators),
                    notes=f"Movimentação de teste" if random.random() > 0.7 else '',
                )
                history.created_at = entry_date
                history.save(update_fields=['created_at'])
                history_entries.append(history)

                quantity_before = quantity_after

    print(f"  {len(history_entries)} entradas de histórico criadas")
    return history_entries


def create_production_orders(materials, users):
    """Criar ordens de produção"""
    print("Criando ordens de produção...")

    orders = []
    admin_user = users[0]
    managers = [u for u in users if 'gerente' in u.username]
    if not managers:
        managers = users

    statuses = ['DRAFT', 'PLANNED', 'PLANNED', 'IN_PROGRESS', 'IN_PROGRESS', 'COMPLETED', 'COMPLETED', 'CANCELLED']

    # Criar 40 ordens de produção com números únicos
    # Agrupar por data para gerar sequências corretas
    order_dates = {}
    for i in range(40):
        material = random.choice(materials)
        status = random.choice(statuses)

        planned_quantity = Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.001'))
        produced_quantity = Decimal('0')

        if status == 'COMPLETED':
            produced_quantity = planned_quantity * Decimal(str(random.uniform(0.95, 1.05))).quantize(Decimal('0.001'))
        elif status == 'IN_PROGRESS':
            produced_quantity = planned_quantity * Decimal(str(random.uniform(0.2, 0.8))).quantize(Decimal('0.001'))

        days_ago = random.randint(0, 60)
        created_date = timezone.now() - timedelta(days=days_ago)
        date_key = created_date.strftime('%Y%m%d')

        # Gerar número da ordem baseado na data
        if date_key not in order_dates:
            order_dates[date_key] = 0
        order_dates[date_key] += 1
        order_number = f"OP-{date_key}-{order_dates[date_key]:03d}"

        planned_start = created_date + timedelta(days=random.randint(1, 7))
        planned_end = planned_start + timedelta(days=random.randint(3, 14))

        actual_start = None
        actual_end = None
        if status in ['IN_PROGRESS', 'COMPLETED']:
            actual_start = planned_start + timedelta(days=random.randint(-2, 3))
        if status == 'COMPLETED':
            actual_end = actual_start + timedelta(days=random.randint(2, 10))

        order = ProductionOrder.objects.create(
            order_number=order_number,
            material=material,
            status=status,
            planned_quantity=planned_quantity,
            produced_quantity=produced_quantity,
            planned_start_date=planned_start.date(),
            planned_end_date=planned_end.date(),
            actual_start_date=actual_start,
            actual_end_date=actual_end,
            responsible=random.choice(managers),
            notes=f"Ordem de produção para {material.code}" if random.random() > 0.5 else '',
            created_by=admin_user,
            updated_by=admin_user,
        )
        order.created_at = created_date
        order.save(update_fields=['created_at'])
        orders.append(order)

    print(f"  {len(orders)} ordens de produção criadas")
    return orders


def create_batches(production_orders, bins, users):
    """Criar bateladas"""
    print("Criando bateladas...")

    batches = []
    admin_user = users[0]
    operators = [u for u in users if 'operador' in u.username]
    if not operators:
        operators = users

    # Criar bateladas para ordens não-rascunho e não-canceladas
    active_orders = [o for o in production_orders if o.status in ['PLANNED', 'IN_PROGRESS', 'COMPLETED']]

    # Agrupar por data para gerar sequências corretas
    batch_dates = {}

    for order in active_orders:
        # 1-3 bateladas por ordem
        num_batches = random.randint(1, 3)
        remaining_quantity = order.planned_quantity

        for i in range(num_batches):
            if remaining_quantity <= 0:
                break

            target_quantity = min(
                Decimal(str(random.uniform(50, 200))).quantize(Decimal('0.001')),
                remaining_quantity
            )
            remaining_quantity -= target_quantity

            # Status baseado no status da ordem
            if order.status == 'COMPLETED':
                batch_status = 'COMPLETED'
            elif order.status == 'IN_PROGRESS':
                batch_status = random.choice(['PREPARATION', 'READY', 'IN_PRODUCTION', 'COMPLETED'])
            else:
                batch_status = random.choice(['PREPARATION', 'READY'])

            actual_quantity = Decimal('0')
            if batch_status in ['READY', 'IN_PRODUCTION', 'COMPLETED']:
                actual_quantity = target_quantity * Decimal(str(random.uniform(0.9, 1.0))).quantize(Decimal('0.001'))

            days_ago = random.randint(0, 30)
            created_date = timezone.now() - timedelta(days=days_ago)
            date_key = created_date.strftime('%Y%m%d')

            # Gerar número da batelada baseado na data
            if date_key not in batch_dates:
                batch_dates[date_key] = 0
            batch_dates[date_key] += 1
            batch_number = f"BAT-{date_key}-{batch_dates[date_key]:03d}"

            batch = Batch.objects.create(
                batch_number=batch_number,
                production_order=order,
                material=order.material,
                status=batch_status,
                target_quantity=target_quantity,
                actual_quantity=actual_quantity,
                prepared_by=random.choice(operators),
                preparation_date=created_date + timedelta(hours=random.randint(1, 24)) if batch_status != 'PREPARATION' else None,
                production_start_date=created_date + timedelta(days=1) if batch_status in ['IN_PRODUCTION', 'COMPLETED'] else None,
                completion_date=created_date + timedelta(days=2) if batch_status == 'COMPLETED' else None,
                notes=f"Batelada {i+1} da ordem {order.order_number}" if random.random() > 0.5 else '',
                created_by=admin_user,
                updated_by=admin_user,
            )
            batch.created_at = created_date
            batch.save(update_fields=['created_at'])
            batches.append(batch)

    print(f"  {len(batches)} bateladas criadas")
    return batches


def create_batch_items(batches, bins, users):
    """Criar itens de batelada"""
    print("Criando itens de batelada...")

    items = []
    operators = [u for u in users if 'operador' in u.username]
    if not operators:
        operators = users

    # Criar itens para bateladas que não estão em preparação
    active_batches = [b for b in batches if b.status != 'PREPARATION']

    for batch in active_batches:
        # Encontrar bins com o material da batelada
        compatible_bins = [b for b in bins if b.current_material == batch.material and b.status in ['LOADED', 'IN_USE']]

        if not compatible_bins:
            # Se não houver bins compatíveis, criar itens "manuais"
            num_items = random.randint(1, 3)
            for _ in range(num_items):
                item = BatchItem.objects.create(
                    batch=batch,
                    bin=None,
                    material=batch.material,
                    quantity=Decimal(str(random.uniform(10, 50))).quantize(Decimal('0.001')),
                    supplier_batch=f"LOTE-{random.randint(2023, 2024)}-{random.randint(1000, 9999)}",
                    certificate=f"CERT-{random.randint(10000, 99999)}" if random.random() > 0.3 else '',
                    collected_by=random.choice(operators),
                    collected_at=batch.created_at + timedelta(hours=random.randint(1, 12)),
                    notes="Item adicionado manualmente" if random.random() > 0.7 else '',
                )
                items.append(item)
        else:
            # Usar bins compatíveis
            num_items = min(random.randint(1, 4), len(compatible_bins))
            selected_bins = random.sample(compatible_bins, num_items)

            for bin_obj in selected_bins:
                item = BatchItem.objects.create(
                    batch=batch,
                    bin=bin_obj,
                    material=batch.material,
                    quantity=Decimal(str(random.uniform(10, 50))).quantize(Decimal('0.001')),
                    supplier_batch=bin_obj.current_supplier_batch,
                    certificate=bin_obj.current_certificate,
                    collected_by=random.choice(operators),
                    collected_at=batch.created_at + timedelta(hours=random.randint(1, 12)),
                    notes=f"Coletado do contentor {bin_obj.code}" if random.random() > 0.5 else '',
                )
                items.append(item)

    print(f"  {len(items)} itens de batelada criados")
    return items


def create_inventory_counts(warehouses, materials, users):
    """Criar contagens de inventário"""
    print("Criando contagens de inventário...")

    counts = []
    admin_user = users[0]
    operators = [u for u in users if 'operador' in u.username or 'qualidade' in u.username]
    if not operators:
        operators = users

    statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'COMPLETED', 'COMPLETED']

    # Agrupar por warehouse e data para gerar sequências corretas
    ref_numbers = {}

    # Criar 20 contagens
    for i in range(20):
        warehouse = random.choice(warehouses)
        status = random.choice(statuses)

        days_ago = random.randint(0, 90)
        count_date = (timezone.now() - timedelta(days=days_ago)).date()

        # Gerar número de referência único
        ref_key = f"{warehouse.code}-{count_date.strftime('%Y%m%d')}"
        if ref_key not in ref_numbers:
            ref_numbers[ref_key] = 0
        ref_numbers[ref_key] += 1
        reference_number = f"INV-{ref_key}-{ref_numbers[ref_key]:03d}"

        counter = random.choice(operators)
        supervisor = random.choice([u for u in users if 'gerente' in u.username or 'admin' in u.username]) if status == 'COMPLETED' else None

        count = InventoryCount.objects.create(
            reference_number=reference_number,
            warehouse=warehouse,
            count_date=count_date,
            status=status,
            counter=counter,
            supervisor=supervisor,
            notes=f"Contagem de inventário #{i+1}" if random.random() > 0.5 else '',
        )
        counts.append(count)

        # Criar itens de contagem
        if status != 'PENDING':
            stocks = MaterialStock.objects.filter(warehouse=warehouse)[:random.randint(5, 15)]

            for stock in stocks:
                system_qty = stock.current_quantity
                counted_qty = system_qty * Decimal(str(random.uniform(0.95, 1.05))).quantize(Decimal('0.001'))

                InventoryCountItem.objects.create(
                    inventory_count=count,
                    material=stock.material,
                    system_quantity=system_qty,
                    counted_quantity=counted_qty if status != 'PENDING' else None,
                    location_code=stock.location_code,
                    notes="Verificado" if status == 'COMPLETED' else '',
                )

    print(f"  {len(counts)} contagens de inventário criadas")
    return counts


def main():
    """Função principal"""
    print("=" * 60)
    print("CRIANDO DADOS DE TESTE PARA O SISTEMA LATECME")
    print("=" * 60)
    print()

    # Criar dados na ordem correta (respeitando dependências)
    users = create_users()
    suppliers = create_suppliers()
    materials = create_materials(suppliers, users)
    warehouses = create_warehouses(users)
    stocks = create_material_stocks(materials, warehouses, users)
    movements = create_stock_movements(materials, warehouses, users)
    reservations = create_stock_reservations(materials, warehouses, users)
    bins = create_bins(warehouses, materials, users)
    bin_history = create_bin_history(bins, materials, users)
    production_orders = create_production_orders(materials, users)
    batches = create_batches(production_orders, bins, users)
    batch_items = create_batch_items(batches, bins, users)
    inventory_counts = create_inventory_counts(warehouses, materials, users)

    print()
    print("=" * 60)
    print("RESUMO DOS DADOS CRIADOS")
    print("=" * 60)
    print(f"  Usuários: {len(users)}")
    print(f"  Fornecedores: {len(suppliers)}")
    print(f"  Materiais: {len(materials)}")
    print(f"  Armazéns: {len(warehouses)}")
    print(f"  Estoques: {len(stocks)}")
    print(f"  Movimentações: {len(movements)}")
    print(f"  Reservas: {len(reservations)}")
    print(f"  Contentores: {len(bins)}")
    print(f"  Histórico de Contentores: {len(bin_history)}")
    print(f"  Ordens de Produção: {len(production_orders)}")
    print(f"  Bateladas: {len(batches)}")
    print(f"  Itens de Batelada: {len(batch_items)}")
    print(f"  Contagens de Inventário: {len(inventory_counts)}")
    print()
    print("Dados de teste criados com sucesso!")
    print()
    print("Credenciais de acesso:")
    print("  Usuário: admin")
    print("  Senha: teste123")
    print()


if __name__ == '__main__':
    main()
