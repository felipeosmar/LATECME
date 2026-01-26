#!/usr/bin/env python
"""
Script para criar dados iniciais do sistema de etiquetas
"""
import os
import sys

# Adiciona o diretório raiz do projeto ao path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import django

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.labels.models import LabelTemplate, PrinterConfiguration
from apps.accounts.models import CustomUser


def create_default_template():
    """Cria template padrão de etiqueta para bins"""

    # Buscar usuário admin
    admin_user = CustomUser.objects.filter(is_superuser=True).first()

    # Verificar se já existe template padrão
    if LabelTemplate.objects.filter(is_default=True).exists():
        print("✓ Template padrão já existe")
        return

    template = LabelTemplate.objects.create(
        name="Etiqueta Padrão Contentor",
        description="Template padrão para etiquetas de contentores com código de barras Code 128",
        width_mm=100,
        height_mm=50,
        printer_dpi=203,
        is_default=True,
        template_json={
            "elements": [
                {
                    "type": "text",
                    "field": "code",
                    "x": 5,
                    "y": 5,
                    "width": 40,
                    "height": 8,
                    "font_size": 4,
                    "font_multiplier_h": 2,
                    "font_multiplier_v": 2,
                    "rotation": 0,
                    "label": ""
                },
                {
                    "type": "barcode",
                    "field": "code",
                    "x": 5,
                    "y": 20,
                    "width": 80,
                    "height": 15,
                    "barcode_type": "128",
                    "human_readable": True,
                    "rotation": 0
                },
                {
                    "type": "text",
                    "field": "warehouse",
                    "x": 5,
                    "y": 40,
                    "width": 30,
                    "height": 6,
                    "font_size": 2,
                    "font_multiplier_h": 1,
                    "font_multiplier_v": 1,
                    "rotation": 0,
                    "label": "Armazém:"
                },
                {
                    "type": "text",
                    "field": "location_code",
                    "x": 50,
                    "y": 40,
                    "width": 40,
                    "height": 6,
                    "font_size": 2,
                    "font_multiplier_h": 1,
                    "font_multiplier_v": 1,
                    "rotation": 0,
                    "label": "Local:"
                }
            ]
        },
        created_by=admin_user,
        updated_by=admin_user
    )

    print(f"✓ Template padrão criado: {template.name}")


def create_example_printer():
    """Cria impressora de exemplo"""

    # Buscar usuário admin
    admin_user = CustomUser.objects.filter(is_superuser=True).first()

    # Verificar se já existe impressora
    if PrinterConfiguration.objects.exists():
        print("✓ Já existem impressoras cadastradas")
        return

    printer = PrinterConfiguration.objects.create(
        name="Impressora Principal",
        ip_address="192.168.1.100",
        port=9100,
        timeout_seconds=5,
        is_default=True,
        created_by=admin_user,
        updated_by=admin_user
    )

    print(f"✓ Impressora de exemplo criada: {printer.name}")
    print(f"  → Conexão: {printer.ip_address}:{printer.port}")
    print(f"  → IMPORTANTE: Configure o IP correto no Django Admin!")


def main():
    print("=" * 60)
    print("Criando dados iniciais do sistema de etiquetas")
    print("=" * 60)
    print()

    try:
        create_default_template()
        create_example_printer()

        print()
        print("=" * 60)
        print("✓ Dados iniciais criados com sucesso!")
        print("=" * 60)
        print()
        print("Próximos passos:")
        print("1. Acesse /admin/labels/printerconfiguration/ para configurar impressoras")
        print("2. Acesse /labels/templates/ para ver templates ou criar novos")
        print("3. Acesse qualquer contentor e clique em 'Imprimir Etiqueta'")
        print()

    except Exception as e:
        print(f"✗ Erro ao criar dados iniciais: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
