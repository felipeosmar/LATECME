#!/usr/bin/env python
"""
Script de diagnóstico de impressora EPL
Testa conectividade e comandos básicos
"""
import socket
import time
import os
import sys
import django

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.labels.models import PrinterConfiguration


def test_connection(ip, port, timeout=5):
    """Testa conexão TCP básica"""
    print(f"\n1. Testando conexão TCP com {ip}:{port}...")
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        print(f"   ✓ Conexão estabelecida com sucesso!")
        return True, sock
    except socket.timeout:
        print(f"   ✗ Timeout ao conectar (>5s)")
        return False, None
    except socket.error as e:
        print(f"   ✗ Erro de conexão: {e}")
        return False, None
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        return False, None


def send_status_request(ip, port):
    """Envia comando para obter status da impressora"""
    print(f"\n2. Solicitando status da impressora...")
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))

        # Comando EPL para status (varia por fabricante)
        # Zebra/Eltron: ~HS (status)
        status_cmd = b'\x1b~HS\r\n'
        sock.sendall(status_cmd)

        # Tentar receber resposta
        sock.settimeout(2)
        try:
            response = sock.recv(1024)
            if response:
                print(f"   ✓ Resposta recebida ({len(response)} bytes):")
                print(f"   {response[:200]}")
            else:
                print(f"   ⚠ Nenhuma resposta (normal em algumas impressoras)")
        except socket.timeout:
            print(f"   ⚠ Sem resposta (timeout - normal em algumas impressoras)")

        return True
    except Exception as e:
        print(f"   ✗ Erro ao solicitar status: {e}")
        return False
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass


def send_test_label_simple(ip, port):
    """Envia etiqueta de teste EPL ultra simples"""
    print(f"\n3. Enviando etiqueta de teste SIMPLES...")

    # EPL mais simples possível
    simple_epl = """N
Q203,16
q203
A10,10,0,3,1,1,N,"TESTE"
P1
"""

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))

        # Codificar e enviar
        encoded = simple_epl.encode('cp850', errors='replace')
        print(f"   Enviando {len(encoded)} bytes...")
        sock.sendall(encoded)

        # Aguardar um pouco
        time.sleep(1)

        print(f"   ✓ EPL enviado com sucesso!")
        print(f"\n   EPL enviado:")
        print(f"   {'-' * 60}")
        for line in simple_epl.strip().split('\n'):
            print(f"   {line}")
        print(f"   {'-' * 60}")
        print(f"\n   ⚠ Verifique se a etiqueta foi impressa na impressora!")

        return True
    except Exception as e:
        print(f"   ✗ Erro ao enviar EPL: {e}")
        return False
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass


def send_test_label_complete(ip, port):
    """Envia etiqueta de teste EPL completa (similar ao sistema)"""
    print(f"\n4. Enviando etiqueta de teste COMPLETA...")

    # EPL similar ao gerado pelo sistema
    complete_epl = """N
Q799,0
q799
A39,39,0,4,2,2,N,"BIN-TESTE"
B39,159,0,1,2,4,119,B,"BIN-TESTE"
A39,319,0,2,1,1,N,"Armazem: ARM-01"
A399,319,0,2,1,1,N,"Local: TESTE"
P1
"""

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))

        # Codificar e enviar
        encoded = complete_epl.encode('cp850', errors='replace')
        print(f"   Enviando {len(encoded)} bytes...")
        sock.sendall(encoded)

        # Aguardar
        time.sleep(1)

        print(f"   ✓ EPL enviado com sucesso!")
        print(f"\n   EPL enviado:")
        print(f"   {'-' * 60}")
        for line in complete_epl.strip().split('\n'):
            print(f"   {line}")
        print(f"   {'-' * 60}")
        print(f"\n   ⚠ Verifique se a etiqueta foi impressa na impressora!")

        return True
    except Exception as e:
        print(f"   ✗ Erro ao enviar EPL: {e}")
        return False
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass


def send_printer_reset(ip, port):
    """Envia comando de reset para a impressora"""
    print(f"\n5. (OPCIONAL) Enviando comando de RESET...")
    print(f"   ⚠ Isso pode limpar configurações da impressora!")
    response = input("   Deseja enviar reset? (s/N): ")

    if response.lower() != 's':
        print("   Pulado.")
        return

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))

        # Comando de reset EPL
        reset_cmd = b'\x1b@\r\n'
        sock.sendall(reset_cmd)

        print(f"   ✓ Comando de reset enviado!")
        print(f"   ⚠ Aguarde alguns segundos para a impressora reiniciar...")

        return True
    except Exception as e:
        print(f"   ✗ Erro ao enviar reset: {e}")
        return False
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass


def diagnose_printer(printer_id=None):
    """Executa diagnóstico completo da impressora"""

    print("=" * 70)
    print("DIAGNÓSTICO DE IMPRESSORA EPL")
    print("=" * 70)

    # Buscar impressora
    if printer_id:
        try:
            printer = PrinterConfiguration.objects.get(id=printer_id, is_active=True)
        except PrinterConfiguration.DoesNotExist:
            print(f"✗ Impressora com ID {printer_id} não encontrada!")
            return
    else:
        printer = PrinterConfiguration.objects.filter(is_active=True).first()
        if not printer:
            print("✗ Nenhuma impressora cadastrada no sistema!")
            print("\nCadastre uma impressora em: /admin/labels/printerconfiguration/")
            return

    print(f"\nImpressora: {printer.name}")
    print(f"IP: {printer.ip_address}")
    print(f"Porta: {printer.port}")
    print(f"Timeout: {printer.timeout_seconds}s")
    print(f"Padrão: {'Sim' if printer.is_default else 'Não'}")

    # Executar testes
    success, sock = test_connection(printer.ip_address, printer.port, printer.timeout_seconds)
    if not success:
        print("\n" + "=" * 70)
        print("✗ FALHA NA CONEXÃO")
        print("=" * 70)
        print("\nVerifique:")
        print("1. IP da impressora está correto?")
        print("2. Impressora está ligada?")
        print("3. Impressora está na mesma rede?")
        print("4. Firewall está bloqueando porta 9100?")
        print(f"5. Testar ping: ping {printer.ip_address}")
        return

    if sock:
        sock.close()

    # Status
    send_status_request(printer.ip_address, printer.port)

    # Etiqueta simples
    send_test_label_simple(printer.ip_address, printer.port)

    # Aguardar
    print("\n⏳ Aguardando 3 segundos...")
    time.sleep(3)

    # Etiqueta completa
    send_test_label_complete(printer.ip_address, printer.port)

    # Reset opcional
    send_printer_reset(printer.ip_address, printer.port)

    # Resumo final
    print("\n" + "=" * 70)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("=" * 70)
    print("\nRESULTADOS:")
    print("- Conexão TCP: ✓ OK")
    print("- Comandos EPL: ✓ Enviados")
    print("\nVERIFIQUE NA IMPRESSORA FÍSICA:")
    print("1. Alguma etiqueta foi impressa?")
    print("2. Há papel/etiquetas carregadas?")
    print("3. Impressora está em modo 'Online'? (não 'Standby')")
    print("4. LED de erro está aceso?")
    print("\nSE NENHUMA ETIQUETA SAIU:")
    print("→ Impressora pode não suportar EPL (pode ser ZPL)")
    print("→ Configuração de DPI pode estar errada")
    print("→ Tamanho da etiqueta configurado pode estar errado")
    print("→ Impressora pode estar em modo de demonstração/teste")
    print("\nPRÓXIMOS PASSOS:")
    print("1. Consulte o manual da impressora")
    print("2. Verifique se é EPL ou ZPL")
    print("3. Configure o tamanho correto da etiqueta na impressora")
    print("4. Verifique se precisa calibrar a impressora")


if __name__ == "__main__":
    try:
        # Permitir passar ID da impressora como argumento
        printer_id = sys.argv[1] if len(sys.argv) > 1 else None
        diagnose_printer(printer_id)
    except KeyboardInterrupt:
        print("\n\n✗ Diagnóstico cancelado pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro durante diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
