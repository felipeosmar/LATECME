from django import forms
from django.core.exceptions import ValidationError
from .models import ProductionOrder, Bin, Batch
from apps.materials.models import Material
from apps.accounts.models import CustomUser
from apps.inventory.models import Warehouse
from decimal import Decimal


class ProductionOrderForm(forms.ModelForm):
    """Formulário para ordens de produção"""

    class Meta:
        model = ProductionOrder
        fields = [
            'material', 'planned_quantity', 'planned_start_date',
            'planned_end_date', 'responsible', 'notes'
        ]
        widgets = {
            'material': forms.Select(attrs={
                'class': 'form-control'
            }),
            'planned_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001'
            }),
            'planned_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'planned_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'responsible': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(is_active=True)
        self.fields['responsible'].queryset = CustomUser.objects.filter(is_active=True)
        self.fields['responsible'].empty_label = "Selecione um responsável"

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('planned_start_date')
        end_date = cleaned_data.get('planned_end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError(
                'Data de início não pode ser posterior à data de fim.'
            )

        return cleaned_data


class BinForm(forms.ModelForm):
    """Formulário para contentores - código é gerado automaticamente"""

    class Meta:
        model = Bin
        fields = ['warehouse', 'capacity', 'location_code', 'notes']
        widgets = {
            'warehouse': forms.Select(attrs={
                'class': 'form-control'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'location_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: A1-B2-P3'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)


class BinLoadForm(forms.Form):
    """Formulário para carregar material em contentor"""
    material = forms.ModelChoiceField(
        queryset=Material.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Material"
    )
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal('0.001'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001'
        }),
        label="Quantidade (kg)"
    )
    supplier_batch = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Lote do fornecedor'
        }),
        label="Lote do Fornecedor"
    )
    certificate = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número do certificado'
        }),
        label="Certificado"
    )


class BatchForm(forms.ModelForm):
    """Formulário para bateladas"""

    class Meta:
        model = Batch
        fields = ['production_order', 'target_quantity', 'notes']
        widgets = {
            'production_order': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apenas ordens ativas (não concluídas/canceladas)
        self.fields['production_order'].queryset = ProductionOrder.objects.filter(
            status__in=['DRAFT', 'PLANNED', 'IN_PROGRESS'],
            is_active=True
        )


class BatchAddBinForm(forms.Form):
    """Formulário para adicionar contentor à batelada"""
    bin_id = forms.UUIDField(
        widget=forms.HiddenInput()
    )
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal('0.001'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001'
        }),
        label="Quantidade (kg)"
    )
