from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Material, Supplier, MaterialSupplier, MaterialCategory, MaterialComposition, ChemicalElement
import json


class MaterialForm(forms.ModelForm):
    """Formulário para criação/edição de materiais"""
    
    specifications_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Ex: {"resistencia_tracao": "310 MPa", "limite_escoamento": "275 MPa"}'
        }),
        required=False,
        help_text='Especificações técnicas em formato JSON',
        label='Especificações Técnicas'
    )
    
    class Meta:
        model = Material
        fields = [
            'code', 'name', 'material_type', 'category', 'density', 
            'melting_point', 'specifications_text',
            'requires_certificate', 'storage_requirements', 'safety_notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: AL7075, TI6AL4V'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do material'
            }),
            'material_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'density': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.1',
                'max': '25'
            }),
            'melting_point': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1'
            }),
            'requires_certificate': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'storage_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'safety_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Preencher campos de texto com dados JSON existentes
        if self.instance and self.instance.pk:
            if self.instance.specifications:
                self.fields['specifications_text'].initial = json.dumps(
                    self.instance.specifications, indent=2, ensure_ascii=False
                )
    
    
    def clean_specifications_text(self):
        specifications_text = self.cleaned_data.get('specifications_text', '')
        if not specifications_text.strip():
            return {}
        
        try:
            specifications = json.loads(specifications_text)
            if not isinstance(specifications, dict):
                raise ValidationError('Especificações devem ser um objeto JSON válido.')
            return specifications
        except json.JSONDecodeError:
            raise ValidationError('Formato JSON inválido para especificações.')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.specifications = self.cleaned_data['specifications_text']
        
        if commit:
            instance.save()
        return instance


class SupplierForm(forms.ModelForm):
    """Formulário para criação/edição de fornecedores"""
    
    class Meta:
        model = Supplier
        fields = [
            'code', 'name', 'cnpj', 'contact_email', 'contact_phone',
            'address', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código interno do fornecedor'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da empresa'
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00.000.000/0000-00'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@empresa.com'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 9999-9999'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Endereço completo'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações gerais'
            }),
        }
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj', '')
        # Remover caracteres não numéricos
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj_clean) != 14:
            raise ValidationError('CNPJ deve ter 14 dígitos.')
        
        # Formatar CNPJ
        return f'{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:14]}'


class MaterialSupplierForm(forms.ModelForm):
    """Formulário para associação Material-Fornecedor"""
    
    class Meta:
        model = MaterialSupplier
        fields = [
            'supplier_code', 'price_per_kg', 'minimum_order', 
            'lead_time_days', 'available', 'notes'
        ]
        widgets = {
            'supplier_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código do fornecedor'
            }),
            'price_per_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'minimum_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'lead_time_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }


class MaterialCategoryForm(forms.ModelForm):
    """Formulário para categorias de materiais"""
    
    class Meta:
        model = MaterialCategory
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }


class MaterialCompositionForm(forms.ModelForm):
    """Formulário para composição de materiais"""
    element = forms.ModelChoiceField(
        queryset=ChemicalElement.objects.all().order_by('symbol'),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Elemento Químico'
    )
    
    class Meta:
        model = MaterialComposition
        fields = ['element', 'percentage', 'is_max']
        widgets = {
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'max': '100.00',
                'placeholder': '0.00'
            }),
            'is_max': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'percentage': 'Percentual (%)',
            'is_max': 'Valor Máximo'
        }


# Formset para composições
MaterialCompositionFormSet = inlineformset_factory(
    Material,
    MaterialComposition,
    form=MaterialCompositionForm,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False,
    fields=['element', 'percentage', 'is_max']
)