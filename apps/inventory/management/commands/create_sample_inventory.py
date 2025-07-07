from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.inventory.models import Warehouse, MaterialStock, StockMovement
from apps.materials.models import Material
from decimal import Decimal
from datetime import datetime
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria dados de exemplo para o módulo de inventário'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Criando dados de exemplo para inventário...'))
        
        # Obter usuário admin
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Usuário admin não encontrado'))
            return
        
        # Criar armazéns
        warehouses_data = [
            {
                'code': 'ARM001',
                'name': 'Armazém Principal',
                'description': 'Armazém principal para materiais em pó',
                'location': 'Setor A - Térreo',
                'manager': admin_user,
            },
            {
                'code': 'ARM002',
                'name': 'Armazém Secundário',
                'description': 'Armazém para materiais especiais',
                'location': 'Setor B - Primeiro Andar',
                'manager': admin_user,
            },
            {
                'code': 'ARM003',
                'name': 'Armazém de Quarentena',
                'description': 'Materiais aguardando certificação',
                'location': 'Setor C - Subsolo',
                'manager': admin_user,
            },
        ]
        
        warehouses = []
        for warehouse_data in warehouses_data:
            warehouse, created = Warehouse.objects.get_or_create(
                code=warehouse_data['code'],
                defaults=warehouse_data
            )
            warehouses.append(warehouse)
            if created:
                self.stdout.write(f'Armazém criado: {warehouse.code} - {warehouse.name}')
        
        # Obter materiais existentes
        materials = list(Material.objects.all())
        if not materials:
            self.stdout.write(self.style.ERROR('Nenhum material encontrado. Execute create_sample_materials primeiro.'))
            return
        
        # Criar estoques iniciais
        self.stdout.write('Criando estoques iniciais...')
        for material in materials:
            for warehouse in warehouses:
                # Nem todos os materiais estão em todos os armazéns
                if random.choice([True, False, True]):  # 2/3 de chance
                    current_quantity = Decimal(str(random.uniform(0, 100)))
                    minimum_stock = Decimal(str(random.uniform(5, 20)))
                    
                    stock, created = MaterialStock.objects.get_or_create(
                        material=material,
                        warehouse=warehouse,
                        defaults={
                            'current_quantity': current_quantity,
                            'minimum_stock': minimum_stock,
                            'maximum_stock': minimum_stock * 5,
                            'location_code': f'{warehouse.code}-{random.randint(1,20):02d}',
                        }
                    )
                    
                    if created:
                        # Criar movimentação de entrada inicial
                        StockMovement.objects.create(
                            material=material,
                            warehouse=warehouse,
                            movement_type='IN',
                            reason='INVENTORY_ADJUSTMENT',
                            quantity=current_quantity,
                            unit_cost=Decimal(str(random.uniform(50, 500))),
                            reference_document='ESTOQUE-INICIAL',
                            notes='Estoque inicial do sistema',
                            user=admin_user,
                        )
                        
                        self.stdout.write(f'Estoque criado: {material.code} em {warehouse.code} - {current_quantity} kg')
        
        # Criar algumas movimentações de exemplo
        self.stdout.write('Criando movimentações de exemplo...')
        
        # Obter alguns estoques com quantidade > 0
        stocks_with_quantity = MaterialStock.objects.filter(current_quantity__gt=0)[:10]
        
        for stock in stocks_with_quantity:
            # Criar algumas movimentações aleatórias
            for _ in range(random.randint(1, 3)):
                movement_type = random.choice(['IN', 'OUT'])
                
                if movement_type == 'IN':
                    quantity = Decimal(str(random.uniform(1, 50)))
                    reason = random.choice(['PURCHASE', 'RETURN', 'PRODUCTION'])
                else:  # OUT
                    # Não tirar mais do que tem
                    max_quantity = min(stock.current_quantity, Decimal('20'))
                    if max_quantity > 0:
                        quantity = Decimal(str(random.uniform(1, float(max_quantity))))
                        reason = random.choice(['PRODUCTION', 'SALE', 'INTERNAL_USE'])
                    else:
                        continue
                
                StockMovement.objects.create(
                    material=stock.material,
                    warehouse=stock.warehouse,
                    movement_type=movement_type,
                    reason=reason,
                    quantity=quantity,
                    unit_cost=Decimal(str(random.uniform(50, 500))),
                    reference_document=f'MOV-{random.randint(1000, 9999)}',
                    notes=f'Movimentação de exemplo - {movement_type}',
                    user=admin_user,
                )
        
        self.stdout.write(self.style.SUCCESS('Dados de exemplo criados com sucesso!'))
        
        # Estatísticas
        total_warehouses = Warehouse.objects.count()
        total_stocks = MaterialStock.objects.count()
        total_movements = StockMovement.objects.count()
        
        self.stdout.write(f'Resumo:')
        self.stdout.write(f'- Armazéns: {total_warehouses}')
        self.stdout.write(f'- Estoques: {total_stocks}')
        self.stdout.write(f'- Movimentações: {total_movements}')