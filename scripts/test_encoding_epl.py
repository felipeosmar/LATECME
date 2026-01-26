#!/usr/bin/env python
"""
Script para testar codificação de caracteres em comandos EPL
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

from apps.labels.models import LabelTemplate
from apps.labels.epl_generator import EPLGenerator
from apps.inventory.models import Bin


def test_encoding():
    """Testa codificação de caracteres portugueses"""

    print("=" * 70)
    print("Teste de Codificação EPL - Caracteres Portugueses")
    print("=" * 70)
    print()

    # Texto de teste com todos os caracteres acentuados
    test_texts = [
        "Armazém Principal",
        "Estação de Trabalho Nº 5",
        "Localização: Área A-15",
        "Capacidade: 50 kg",
        "Status: Vazio",
        "Código: BIN-001",
        "Descrição completa com àáâãéêíóôõúç",
    ]

    print("Testando caracteres individuais:")
    print("-" * 70)

    for text in test_texts:
        print(f"\nTexto original: {text}")

        # Testar ASCII (antigo - deve falhar)
        try:
            ascii_encoded = text.encode('ascii')
            print(f"  ✓ ASCII: {ascii_encoded}")
        except UnicodeEncodeError as e:
            print(f"  ✗ ASCII: ERRO - {e.reason} (esperado)")

        # Testar CP850 (novo - deve funcionar)
        try:
            cp850_encoded = text.encode('cp850', errors='replace')
            print(f"  ✓ CP850: {len(cp850_encoded)} bytes codificados")
        except Exception as e:
            print(f"  ✗ CP850: ERRO - {str(e)}")

        # Testar Latin-1 (fallback - deve funcionar)
        try:
            latin1_encoded = text.encode('latin-1', errors='replace')
            print(f"  ✓ Latin-1: {len(latin1_encoded)} bytes codificados")
        except Exception as e:
            print(f"  ✗ Latin-1: ERRO - {str(e)}")

    print()
    print("=" * 70)

    # Testar com bin real se existir
    print("\nTestando com bin real:")
    print("-" * 70)

    bin_obj = Bin.objects.filter(is_active=True).first()

    if bin_obj:
        print(f"\nBin encontrado: {bin_obj.code}")
        print(f"  - Armazém: {bin_obj.warehouse.code if bin_obj.warehouse else 'N/A'}")
        print(f"  - Localização: {bin_obj.location_code or 'N/A'}")
        print(f"  - Status: {bin_obj.get_status_display()}")

        # Testar com template se existir
        template = LabelTemplate.objects.filter(is_active=True).first()

        if template:
            print(f"\nTemplate encontrado: {template.name}")

            # Gerar EPL
            generator = EPLGenerator(template, bin_obj)
            epl_content = generator.generate()

            print(f"\nComandos EPL gerados ({len(epl_content)} caracteres):")
            print("-" * 70)
            print(epl_content[:500] + "..." if len(epl_content) > 500 else epl_content)
            print("-" * 70)

            # Testar codificação do EPL completo
            print("\nTestando codificação do EPL completo:")

            try:
                cp850_epl = epl_content.encode('cp850', errors='replace')
                print(f"  ✓ CP850: {len(cp850_epl)} bytes")
            except Exception as e:
                print(f"  ✗ CP850: ERRO - {str(e)}")

            try:
                latin1_epl = epl_content.encode('latin-1', errors='replace')
                print(f"  ✓ Latin-1: {len(latin1_epl)} bytes")
            except Exception as e:
                print(f"  ✗ Latin-1: ERRO - {str(e)}")

            try:
                ascii_epl = epl_content.encode('ascii')
                print(f"  ✓ ASCII: {len(ascii_epl)} bytes")
            except UnicodeEncodeError as e:
                print(f"  ✗ ASCII: ERRO - {e.reason} (esperado se houver acentos)")

        else:
            print("\n⚠ Nenhum template encontrado. Execute create_labels_initial_data.py")
    else:
        print("\n⚠ Nenhum bin encontrado no banco de dados.")

    print()
    print("=" * 70)
    print("Teste concluído!")
    print("=" * 70)
    print()

    print("Resumo:")
    print("- ✓ CP850: Codificação recomendada para impressoras EPL/ZPL")
    print("- ✓ Latin-1: Fallback automático se CP850 falhar")
    print("- ✗ ASCII: Não suporta acentos (erro esperado)")
    print()
    print("Se todos os testes CP850 passaram, a impressão deve funcionar!")


if __name__ == "__main__":
    try:
        test_encoding()
    except Exception as e:
        print(f"\n✗ Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
