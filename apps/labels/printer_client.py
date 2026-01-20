"""
Módulo para comunicação TCP/IP com impressoras EPL
"""
import socket
from django.utils import timezone


class PrinterClient:
    """Cliente TCP/IP para comunicação com impressoras EPL"""

    def __init__(self, printer_config):
        """
        Inicializa o cliente da impressora

        Args:
            printer_config: Instância de PrinterConfiguration
        """
        self.config = printer_config
        self.ip = printer_config.ip_address
        self.port = printer_config.port
        self.timeout = printer_config.timeout_seconds

    def send_epl(self, epl_content):
        """
        Envia comandos EPL para a impressora

        Args:
            epl_content: String com comandos EPL

        Returns:
            tuple: (success: bool, error_message: str)
        """
        sock = None
        try:
            # Criar socket TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            # Conectar à impressora
            sock.connect((self.ip, self.port))

            # Enviar comandos EPL
            # Usar cp850 (Code Page 850) que é padrão em impressoras térmicas
            # e suporta caracteres portugueses (é, ã, ç, etc.)
            # Se falhar, usa latin-1 como fallback
            # errors='replace' substitui caracteres não suportados por '?'
            try:
                encoded_data = epl_content.encode('cp850', errors='replace')
            except (UnicodeEncodeError, LookupError):
                # Fallback para latin-1 se cp850 não estiver disponível
                encoded_data = epl_content.encode('latin-1', errors='replace')

            sock.sendall(encoded_data)

            return (True, '')

        except socket.timeout:
            error_msg = f"Timeout ao conectar com impressora {self.ip}:{self.port}"
            return (False, error_msg)

        except socket.error as e:
            error_msg = f"Erro de conexão com impressora: {str(e)}"
            return (False, error_msg)

        except Exception as e:
            error_msg = f"Erro ao enviar EPL: {str(e)}"
            return (False, error_msg)

        finally:
            # Sempre fechar socket
            if sock:
                try:
                    sock.close()
                except:
                    pass

    def test_connection(self):
        """
        Testa conectividade com a impressora

        Returns:
            tuple: (success: bool, message: str)
        """
        sock = None
        try:
            # Criar socket TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            # Tentar conectar
            sock.connect((self.ip, self.port))

            # Atualizar status no banco de dados
            self.config.last_test_date = timezone.now()
            self.config.last_test_success = True
            self.config.save(update_fields=['last_test_date', 'last_test_success'])

            return (True, f"Conexão bem-sucedida com {self.ip}:{self.port}")

        except socket.timeout:
            error_msg = f"Timeout ao conectar com {self.ip}:{self.port}"
            self.config.last_test_date = timezone.now()
            self.config.last_test_success = False
            self.config.save(update_fields=['last_test_date', 'last_test_success'])
            return (False, error_msg)

        except socket.error as e:
            error_msg = f"Erro de conexão: {str(e)}"
            self.config.last_test_date = timezone.now()
            self.config.last_test_success = False
            self.config.save(update_fields=['last_test_date', 'last_test_success'])
            return (False, error_msg)

        except Exception as e:
            error_msg = f"Erro ao testar conexão: {str(e)}"
            self.config.last_test_date = timezone.now()
            self.config.last_test_success = False
            self.config.save(update_fields=['last_test_date', 'last_test_success'])
            return (False, error_msg)

        finally:
            # Sempre fechar socket
            if sock:
                try:
                    sock.close()
                except:
                    pass
