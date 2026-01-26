#!/usr/bin/env python
"""
Script para testar impressão real usando o código do sistema
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

from apps.labels.models import LabelTemplate, PrinterConfiguration, PrintJob
from apps.inventory.models import Bin
from apps.labels.epl_generator import EPLGenerator
from apps.labels.printer_client import PrinterClient
from django.utils import timezone


def test_real_print():
    """Testa impressão real usando exatamente o mesmo código do sistema"""

    print("=" * 70)
    print("TESTE DE IMPRESSÃO REAL - SISTEMA LATECME")
    print("=" * 70)

    # 1. Buscar bin
    print("\n1. Buscando bin de teste...")
    bin_obj = Bin.objects.filter(is_active=True).first()
    if not bin_obj:
        print("   ✗ Nenhum bin encontrado no banco de dados!")
        return

    print(f"   ✓ Bin encontrado: {bin_obj.code}")
    print(f"     - Armazém: {bin_obj.warehouse.code if bin_obj.warehouse else 'N/A'}")
    print(f"     - Localização: {bin_obj.location_code or 'N/A'}")
    print(f"     - Status: {bin_obj.get_status_display()}")

    # 2. Buscar template
    print("\n2. Buscando template...")
    template = LabelTemplate.objects.filter(is_active=True, is_default=True).first()
    if not template:
        template = LabelTemplate.objects.filter(is_active=True).first()

    if not template:
        print("   ✗ Nenhum template encontrado!")
        print("   Execute: venv/bin/python create_labels_initial_data.py")
        return

    print(f"   ✓ Template encontrado: {template.name}")
    print(f"     - Dimensões: {template.width_mm}x{template.height_mm}mm")
    print(f"     - DPI: {template.printer_dpi}")
    print(f"     - Elementos: {len(template.template_json.get('elements', []))}")

    # 3. Buscar impressora
    print("\n3. Buscando impressora...")
    printer = PrinterConfiguration.objects.filter(is_active=True, is_default=True).first()
    if not printer:
        printer = PrinterConfiguration.objects.filter(is_active=True).first()

    if not printer:
        print("   ✗ Nenhuma impressora encontrada!")
        print("   Configure em: /admin/labels/printerconfiguration/")
        return

    print(f"   ✓ Impressora encontrada: {printer.name}")
    print(f"     - Conexão: {printer.ip_address}:{printer.port}")
    print(f"     - Timeout: {printer.timeout_seconds}s")

    # 4. Gerar EPL (EXATAMENTE como o sistema faz)
    print("\n4. Gerando comandos EPL...")
    generator = EPLGenerator(template, bin_obj)
    epl_content = generator.generate()  # Usando enhanced_mode=True (padrão)

    print(f"   ✓ EPL gerado ({len(epl_content)} caracteres)")
    print("\n   Comandos EPL:")
    print("   " + "-" * 66)
    for line in epl_content.split('\n'):
        print(f"   {line}")
    print("   " + "-" * 66)

    # 5. Confirmar impressão
    print("\n5. Pronto para imprimir!")
    print(f"\n   Bin: {bin_obj.code}")
    print(f"   Template: {template.name}")
    print(f"   Impressora: {printer.name} ({printer.ip_address}:{printer.port})")

    response = input("\n   Deseja IMPRIMIR AGORA? (s/N): ")
    if response.lower() != 's':
        print("\n   Impressão cancelada pelo usuário.")
        return

    # 6. Criar PrintJob (EXATAMENTE como o sistema faz)
    print("\n6. Criando PrintJob...")
    bin_snapshot = generator.get_bin_snapshot()

    print_job = PrintJob(
        printer=printer,
        template=template,
        bin=bin_obj,
        status='PROCESSING',
        epl_content=epl_content,
        bin_data_snapshot=bin_snapshot,
        created_by=None,  # Script não tem user
        updated_by=None
    )
    print_job.save()

    print(f"   ✓ PrintJob criado: {print_job.id}")
    print(f"     - Status: {print_job.status}")

    # 7. Enviar para impressora (EXATAMENTE como o sistema faz)
    print("\n7. Enviando para impressora...")
    client = PrinterClient(printer)
    success, error_message = client.send_epl(epl_content)

    # 8. Atualizar PrintJob (EXATAMENTE como o sistema faz)
    if success:
        print_job.status = 'SUCCESS'
        print_job.printed_at = timezone.now()
        print(f"   ✓ EPL enviado com SUCESSO!")
    else:
        print_job.status = 'FAILED'
        print_job.error_message = error_message
        print(f"   ✗ FALHA ao enviar EPL:")
        print(f"     {error_message}")

    print_job.save()

    # 9. Resultado final
    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    print(f"\nPrintJob ID: {print_job.id}")
    print(f"Status: {print_job.status}")

    if success:
        print(f"\n✓ SUCESSO! Comandos EPL enviados para a impressora.")
        print(f"\n⚠ VERIFIQUE A IMPRESSORA FÍSICA:")
        print(f"  1. Alguma etiqueta foi impressa?")
        print(f"  2. A etiqueta está correta?")
        print(f"  3. Texto legível?")
        print(f"  4. Código de barras impresso?")
        print(f"\nSe a etiqueta NÃO saiu:")
        print(f"  → Consulte: TROUBLESHOOT_PRINTER.md")
        print(f"  → Execute auto-teste da impressora")
        print(f"  → Verifique se há papel/etiquetas")
        print(f"\nSe a etiqueta saiu mas está ERRADA:")
        print(f"  → Ajuste template em: /admin/labels/labeltemplate/")
        print(f"  → Verifique DPI (203 vs 300)")
        print(f"  → Verifique tamanho da etiqueta física")
    else:
        print(f"\n✗ FALHA na comunicação com a impressora!")
        print(f"\nErro: {error_message}")
        print(f"\nVerifique:")
        print(f"  - IP está correto? ({printer.ip_address})")
        print(f"  - Impressora está ligada?")
        print(f"  - Impressora está na rede?")

    print(f"\nPrintJob pode ser visualizado em:")
    print(f"  /admin/labels/printjob/{print_job.id}/change/")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_real_print()
    except KeyboardInterrupt:
        print("\n\n✗ Teste cancelado pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
