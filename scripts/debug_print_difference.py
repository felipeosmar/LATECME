#!/usr/bin/env python
"""
Script para debug: descobrir diferença entre web e script
"""
import os
import sys

# Adiciona o diretório raiz do projeto ao path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import django
import socket
import time

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.labels.models import LabelTemplate, PrinterConfiguration
from apps.inventory.models import Bin
from apps.labels.epl_generator import EPLGenerator


def test_with_different_timings():
    """Testa impressão com diferentes timings"""

    print("=" * 70)
    print("DEBUG: TESTE DE TIMING - Descobrir delay necessário")
    print("=" * 70)

    # Buscar objetos
    bin_obj = Bin.objects.filter(is_active=True).first()
    template = LabelTemplate.objects.filter(is_active=True).first()
    printer = PrinterConfiguration.objects.filter(is_active=True).first()

    if not all([bin_obj, template, printer]):
        print("✗ Faltam dados no banco (bin/template/printer)")
        return

    print(f"\nUsando:")
    print(f"  Bin: {bin_obj.code}")
    print(f"  Template: {template.name}")
    print(f"  Impressora: {printer.name} ({printer.ip_address}:{printer.port})")

    # Gerar EPL
    generator = EPLGenerator(template, bin_obj)
    epl_content = generator.generate()

    print(f"\nEPL gerado ({len(epl_content)} chars)")

    # Codificar
    try:
        encoded_data = epl_content.encode('cp850', errors='replace')
    except:
        encoded_data = epl_content.encode('latin-1', errors='replace')

    # Testar com diferentes delays
    delays = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]

    for delay in delays:
        print(f"\n{'=' * 70}")
        print(f"TESTE {delays.index(delay) + 1}/{len(delays)}: Delay de {delay}s")
        print(f"{'=' * 70}")

        response = input(f"\nPressione ENTER para testar com delay de {delay}s (ou 's' para pular): ")
        if response.lower() == 's':
            print("Pulado.")
            continue

        sock = None
        try:
            # Conectar
            print(f"\n1. Conectando...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(printer.timeout_seconds)
            sock.connect((printer.ip_address, printer.port))
            print(f"   ✓ Conectado")

            # Enviar
            print(f"2. Enviando {len(encoded_data)} bytes...")
            start_time = time.time()
            sock.sendall(encoded_data)
            send_time = time.time() - start_time
            print(f"   ✓ Enviado em {send_time*1000:.2f}ms")

            # Shutdown
            print(f"3. Shutdown do socket (flush)...")
            try:
                sock.shutdown(socket.SHUT_WR)
                print(f"   ✓ Shutdown OK")
            except Exception as e:
                print(f"   ⚠ Shutdown falhou: {e}")

            # Delay
            print(f"4. Aguardando {delay}s...")
            time.sleep(delay)
            print(f"   ✓ Delay concluído")

            # Fechar
            print(f"5. Fechando socket...")
            sock.close()
            print(f"   ✓ Fechado")

            # Verificar com usuário
            print(f"\n{'*' * 70}")
            print(f"VERIFICAÇÃO MANUAL:")
            print(f"{'*' * 70}")
            result = input(f"\nA etiqueta SAIU DA IMPRESSORA? (s/N): ")

            if result.lower() == 's':
                print(f"\n🎉 SUCESSO! Delay de {delay}s funciona!")
                print(f"\n✓ Delay mínimo necessário: {delay}s")
                print(f"\nAtualize printer_client.py para:")
                print(f"   time.sleep({delay})")

                confirm = input(f"\nDeseja continuar testando delays maiores? (s/N): ")
                if confirm.lower() != 's':
                    break
            else:
                print(f"\n✗ Não imprimiu com delay de {delay}s")
                print(f"Continuando para próximo delay...")

        except Exception as e:
            print(f"\n✗ Erro: {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

        # Pausa entre testes
        if delay != delays[-1]:
            input("\nPressione ENTER para continuar para próximo teste...")

    print(f"\n{'=' * 70}")
    print("DIAGNÓSTICO CONCLUÍDO")
    print(f"{'=' * 70}")

    print("\nRESUMO:")
    print("Se NENHUM delay funcionou:")
    print("  → Problema NÃO é timing")
    print("  → Pode ser diferença no contexto de execução (Django web vs script)")
    print("  → Pode ser necessário adicionar linha em branco ao final do EPL")
    print("  → Pode ser necessário adicionar comando de feed (F)")
    print("\nSe algum delay funcionou:")
    print("  → Anote o delay mínimo que funcionou")
    print("  → Atualize printer_client.py com esse valor")


if __name__ == "__main__":
    try:
        test_with_different_timings()
    except KeyboardInterrupt:
        print("\n\n✗ Teste cancelado.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
