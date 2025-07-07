from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    Warehouse, MaterialStock, StockMovement, 
    StockReservation, InventoryCount
)
from apps.materials.models import Material
from apps.accounts.models import CustomUser
from decimal import Decimal


class WarehouseForm(forms.ModelForm):
    """Formulário para armazéns"""
    
    class Meta:
        model = Warehouse
        fields = ['code', 'name', 'description', 'location', 'manager', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código do armazém'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do armazém'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Localização física'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas usuários ativos
        self.fields['manager'].queryset = CustomUser.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['manager'].empty_label = "Selecione um responsável"


class MaterialStockForm(forms.ModelForm):
    """Formulário para estoque de materiais"""
    
    class Meta:
        model = MaterialStock
        fields = [
            'material', 'warehouse', 'current_quantity', 
            'minimum_stock', 'maximum_stock', 'location_code'
        ]
        widgets = {
            'material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'current_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'minimum_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'maximum_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'location_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: A1-B2'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(
            is_active=True
        ).order_by('code')
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            is_active=True
        ).order_by('code')
    
    def clean(self):
        cleaned_data = super().clean()
        minimum_stock = cleaned_data.get('minimum_stock')
        maximum_stock = cleaned_data.get('maximum_stock')
        
        if minimum_stock and maximum_stock:
            if minimum_stock > maximum_stock:
                raise ValidationError(
                    'O estoque mínimo não pode ser maior que o estoque máximo.'
                )
        
        return cleaned_data


class StockMovementForm(forms.ModelForm):
    """Formulário para movimentações de estoque"""
    
    class Meta:
        model = StockMovement
        fields = [
            'material', 'warehouse', 'movement_type', 'reason',
            'quantity', 'unit_cost', 'batch_number', 'expiry_date',
            'certificate_number', 'reference_document', 'notes',
            'destination_warehouse'
        ]
        widgets = {
            'material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'movement_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'reason': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número do lote'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'certificate_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número do certificado'
            }),
            'reference_document': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NF, pedido, etc.'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações'
            }),
            'destination_warehouse': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(
            is_active=True
        ).order_by('code')
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            is_active=True
        ).order_by('code')
        self.fields['destination_warehouse'].queryset = Warehouse.objects.filter(
            is_active=True
        ).order_by('code')
        self.fields['destination_warehouse'].empty_label = "Selecione (apenas para transferências)"
    
    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        destination_warehouse = cleaned_data.get('destination_warehouse')
        warehouse = cleaned_data.get('warehouse')
        material = cleaned_data.get('material')
        quantity = cleaned_data.get('quantity')
        
        # Validar transferência
        if movement_type == 'TRANSFER':
            if not destination_warehouse:
                raise ValidationError(
                    'Armazém de destino é obrigatório para transferências.'
                )
            if destination_warehouse == warehouse:
                raise ValidationError(
                    'Armazém de destino deve ser diferente do armazém de origem.'
                )
        
        # Validar estoque suficiente para saídas
        if movement_type in ['OUT', 'TRANSFER'] and material and warehouse and quantity:
            try:
                stock = MaterialStock.objects.get(
                    material=material,
                    warehouse=warehouse
                )
                if stock.available_quantity < quantity:
                    raise ValidationError(
                        f'Estoque insuficiente. Disponível: {stock.available_quantity} kg'
                    )
            except MaterialStock.DoesNotExist:
                raise ValidationError(
                    'Material não encontrado no estoque do armazém selecionado.'
                )
        
        return cleaned_data


class StockReservationForm(forms.ModelForm):
    """Formulário para reservas de estoque"""
    
    class Meta:
        model = StockReservation
        fields = [
            'material', 'warehouse', 'quantity', 'expiry_date',
            'purpose', 'reference_document', 'notes'
        ]
        widgets = {
            'material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001'
            }),
            'expiry_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'purpose': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Finalidade da reserva'
            }),
            'reference_document': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Documento de referência'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(
            is_active=True
        ).order_by('code')
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            is_active=True
        ).order_by('code')
    
    def clean(self):
        cleaned_data = super().clean()
        material = cleaned_data.get('material')
        warehouse = cleaned_data.get('warehouse')
        quantity = cleaned_data.get('quantity')
        expiry_date = cleaned_data.get('expiry_date')
        
        # Validar data de expiração
        if expiry_date and expiry_date <= timezone.now():
            raise ValidationError(
                'A data de expiração deve ser futura.'
            )
        
        # Validar estoque disponível
        if material and warehouse and quantity:
            try:
                stock = MaterialStock.objects.get(
                    material=material,
                    warehouse=warehouse
                )
                if not stock.can_reserve(quantity):
                    raise ValidationError(
                        f'Estoque insuficiente para reserva. Disponível: {stock.available_quantity} kg'
                    )
            except MaterialStock.DoesNotExist:
                raise ValidationError(
                    'Material não encontrado no estoque do armazém selecionado.'
                )
        
        return cleaned_data


class InventoryCountForm(forms.ModelForm):
    """Formulário para contagem de inventário"""
    
    class Meta:
        model = InventoryCount
        fields = [
            'warehouse', 'count_date', 'counter', 'supervisor', 'notes'
        ]
        widgets = {
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'count_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'counter': forms.Select(attrs={
                'class': 'form-control'
            }),
            'supervisor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a contagem'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warehouse'].queryset = Warehouse.objects.filter(
            is_active=True
        ).order_by('code')
        self.fields['counter'].queryset = CustomUser.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['supervisor'].queryset = CustomUser.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['counter'].empty_label = "Selecione o contador"
        self.fields['supervisor'].empty_label = "Selecione o supervisor"
    
    def clean(self):
        cleaned_data = super().clean()
        counter = cleaned_data.get('counter')
        supervisor = cleaned_data.get('supervisor')
        
        if counter and supervisor and counter == supervisor:
            raise ValidationError(
                'O contador e o supervisor devem ser pessoas diferentes.'
            )
        
        return cleaned_data


class StockSearchForm(forms.Form):
    """Formulário para busca de estoque"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código, nome ou armazém'
        })
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True),
        required=False,
        empty_label="Todos os armazéns",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    material_type = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + Material.MATERIAL_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    stock_status = forms.ChoiceField(
        choices=[
            ('', 'Todos os status'),
            ('normal', 'Normal'),
            ('low', 'Estoque Baixo'),
            ('out', 'Sem Estoque'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )