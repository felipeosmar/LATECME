#!/usr/bin/env python
"""
Script que simula EXATAMENTE uma requisição web de impressão
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

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.labels.views import print_label
from apps.labels.models import LabelTemplate, PrinterConfiguration, PrintJob
from apps.inventory.models import Bin
import json


def simulate_web_print():
    """Simula requisição AJAX POST exatamente como o navegador faz"""

    print("=" * 70)
    print("SIMULAÇÃO DE REQUISIÇÃO WEB - Idêntica ao navegador")
    print("=" * 70)

    # Buscar objetos
    bin_obj = Bin.objects.filter(is_active=True).first()
    template = LabelTemplate.objects.filter(is_active=True).first()
    printer = PrinterConfiguration.objects.filter(is_active=True).first()
    user = get_user_model().objects.filter(is_superuser=True).first()

    if not all([bin_obj, template, printer]):
        print("✗ Faltam dados no banco")
        return

    print(f"\nDados da requisição:")
    print(f"  Bin: {bin_obj.code} ({bin_obj.id})")
    print(f"  Template: {template.name} ({template.id})")
    print(f"  Impressora: {printer.name} ({printer.id})")
    print(f"  User: {user.username if user else 'None'}")

    # Criar factory de requisição
    factory = RequestFactory()

    # Dados da requisição (idênticos ao JavaScript)
    request_data = {
        'bin_id': str(bin_obj.id),
        'template_id': str(template.id),
        'printer_id': str(printer.id)
    }

    print(f"\nJSON enviado:")
    print(json.dumps(request_data, indent=2))

    # Criar requisição POST AJAX (idêntica ao navegador)
    request = factory.post(
        '/labels/print/execute/',
        data=json.dumps(request_data),
        content_type='application/json',
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # Header AJAX
    )

    # Adicionar usuário autenticado
    if user:
        request.user = user
    else:
        print("\n⚠ Nenhum superuser encontrado, criando mock user...")
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    print(f"\n{'=' * 70}")
    print("EXECUTANDO VIEW print_label() - Exatamente como Django faz")
    print(f"{'=' * 70}")

    try:
        # Chamar a view (EXATAMENTE como Django faz)
        response = print_label(request)

        print(f"\nResposta da view:")
        print(f"  Status code: {response.status_code}")
        print(f"  Content-Type: {response.get('Content-Type')}")

        # Parsear resposta JSON
        response_data = json.loads(response.content)
        print(f"\nJSON retornado:")
        print(json.dumps(response_data, indent=2))

        if response_data.get('success'):
            print(f"\n✓ View retornou SUCCESS!")

            # Buscar PrintJob criado
            print_job_id = response_data.get('print_job_id')
            if print_job_id:
                print_job = PrintJob.objects.get(id=print_job_id)
                print(f"\nPrintJob criado:")
                print(f"  ID: {print_job.id}")
                print(f"  Status: {print_job.status}")
                print(f"  Printed at: {print_job.printed_at}")
                print(f"  Error: {print_job.error_message or 'Nenhum'}")

                print(f"\nEPL enviado ({len(print_job.epl_content)} chars):")
                print("-" * 70)
                print(print_job.epl_content)
                print("-" * 70)

        else:
            print(f"\n✗ View retornou FALHA!")
            print(f"Erro: {response_data.get('message')}")

    except Exception as e:
        print(f"\n✗ Erro ao executar view: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verificação manual
    print(f"\n{'*' * 70}")
    print("VERIFICAÇÃO MANUAL")
    print(f"{'*' * 70}")

    result = input("\nA etiqueta SAIU DA IMPRESSORA FÍSICA? (s/N): ")

    if result.lower() == 's':
        print("\n🎉 SUCESSO! Simulação web funciona!")
        print("\nIsso significa que:")
        print("  ✓ O código da view está correto")
        print("  ✓ O problema pode ser no navegador/JavaScript")
        print("  ✓ Ou pode ser cache do navegador")
        print("\nSoluções:")
        print("  1. Limpar cache do navegador (Ctrl+Shift+Delete)")
        print("  2. Testar em aba anônima (Ctrl+Shift+N)")
        print("  3. Verificar console do navegador (F12)")
        print("  4. Recarregar aplicação (Ctrl+F5)")
    else:
        print("\n✗ Simulação web TAMBÉM não funciona!")
        print("\nIsso confirma que:")
        print("  ✗ Problema NÃO é específico do navegador")
        print("  ✗ Problema está no código Python ou impressora")
        print("\nPróximos passos:")
        print("  1. Execute: venv/bin/python debug_print_difference.py")
        print("  2. Teste diferentes delays manualmente")
        print("  3. Verifique se precisa de comando FEED adicional")
        print("  4. Consulte manual da impressora sobre EPL")

    print(f"\n{'=' * 70}")


if __name__ == "__main__":
    try:
        simulate_web_print()
    except KeyboardInterrupt:
        print("\n\n✗ Teste cancelado.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
