#!/usr/bin/env python
"""
Script para limpar sessões antigas do Django
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

from django.contrib.sessions.models import Session


def clear_all_sessions():
    """Remove todas as sessões do banco de dados"""
    count = Session.objects.all().count()
    Session.objects.all().delete()
    print(f"✓ {count} sessões removidas com sucesso!")
    print()
    print("Próximos passos:")
    print("1. Reinicie o servidor Django se estiver rodando")
    print("2. Limpe os cookies do navegador (Ctrl+Shift+Delete)")
    print("3. Acesse http://127.0.0.1:8000/ novamente")
    print()
    print("O erro de ERR_TOO_MANY_REDIRECTS deve estar corrigido!")


if __name__ == "__main__":
    print("=" * 60)
    print("Limpando sessões antigas do Django")
    print("=" * 60)
    print()

    try:
        clear_all_sessions()
    except Exception as e:
        print(f"✗ Erro ao limpar sessões: {str(e)}")
        sys.exit(1)
