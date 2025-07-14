# LATECME - Sistema de Controle de Manufatura

Sistema Django para controle de manufatura aditiva de materiais metálicos, com foco em gestão de estoque de ligas metálicas, rastreamento de materiais, geração de códigos de barras e integração com hardware.

## Requisitos do Sistema

### Tecnologias Principais
- **Python**: 3.10 ou superior
- **Django**: 5.2.4 ou superior
- **Banco de Dados**: PostgreSQL (recomendado) ou SQLite (desenvolvimento)
- **Poetry**: Gerenciador de dependências (recomendado)
- **Docker**: Para banco de dados PostgreSQL (opcional)

### Dependências de Sistema
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip postgresql postgresql-contrib

## Instalação

### 1. Clonagem do Projeto
```bash
git clone <url-do-repositorio>
cd LATECME
```

### 2. Configuração do Ambiente Python

#### Usando Poetry
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependências
poetry install

# Ativar ambiente virtual
poetry shell
```

### 3. Configuração do Banco de Dados

#### Opção A: PostgreSQL com Docker (Recomendado)
```bash
# Criar arquivo .env na raiz do projeto
touch .env

# Iniciar serviços PostgreSQL
docker-compose -f docker-compose-dev.yml up -d

# Verificar se os serviços estão rodando
docker-compose -f docker-compose-dev.yml ps
```
### 4. Configuração do Django

```bash
# Aplicar migrações
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar dados iniciais (opcional)
python create_initial_data.py
python create_materials_data.py
```

### 5. Inicialização do Sistema

```bash
# Iniciar servidor de desenvolvimento
python manage.py runserver

# O sistema estará disponível em: http://localhost:8000
# Admin Django: http://localhost:8000/admin
```

## Estrutura do Projeto

```
LATECME/
├── apps/                           # Aplicações Django
│   ├── core/                      # Modelos base e utilitários
│   ├── accounts/                  # Gerenciamento de usuários
│   ├── materials/                 # Gestão de materiais e fornecedores
│   └── inventory/                 # Controle de estoque
├── config/                        # Configurações Django
│   ├── settings.py               # Configurações principais
│   └── urls.py                   # URLs principais
├── templates/                     # Templates HTML
├── color-admin/                   # Template Bootstrap
├── Documentacao/                  # Documentação do sistema
├── manage.py                      # Script de gerenciamento Django
├── pyproject.toml                 # Configuração Poetry
└── docker-compose-dev.yml         # Configuração Docker
```

## Funcionalidades Principais

### Gestão de Materiais
- Cadastro de materiais com códigos únicos (AL7075, TI6AL4, etc.)
- Tipos suportados: Alumínio (AL), Titânio (TI), Aço Inox (SS), Inconel (IN), Cobalto-Cromo (CO)
- Controle de composição, densidade e certificações

### Controle de Estoque
- Itens de estoque com códigos de barras únicos
- Rastreamento de peso, lote do fornecedor, localização
- Fluxo de status: Registrado → Disponível → Reservado → Consumido
- Suporte a quarentena e descarte

### Gestão de Fornecedores
- Cadastro de fornecedores com informações de contato
- Controle de preços e prazos de entrega
- Histórico de compras

## Configurações Avançadas

### Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com:

```env
# Configurações do Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Configurações do Banco de Dados
DB_NAME=latecme_db
DB_USER=latecme_user
DB_PASSWORD=latecme_password
DB_HOST=localhost
DB_PORT=5432

# Configurações Redis (para produção)
REDIS_URL=redis://localhost:6379/0
```

### Configuração para Produção
```bash
# Instalar servidor web
pip install gunicorn

# Configurar variáveis de ambiente
export DEBUG=False
export ALLOWED_HOSTS=seu-dominio.com

# Iniciar com Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Desenvolvimento

### Estrutura de Usuários
O sistema possui um modelo de usuário customizado com os seguintes perfis:
- **Operador**: Acesso ao estoque e movimentações
- **Administrador**: Acesso completo ao sistema
- **Comprador**: Acesso a compras e fornecedores

### Comandos Úteis
```bash
# Criar nova migração
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Acessar shell Django
python manage.py shell

# Executar testes
python manage.py test

# Verificar problemas
python manage.py check
```

## Solução de Problemas

### Erro: "No module named 'django'"
```bash
# Verificar se o ambiente virtual está ativado
poetry shell  # ou source venv/bin/activate

# Reinstalar Django
pip install django>=5.2.4
```

### Erro de Banco de Dados
```bash
# Verificar se PostgreSQL está rodando
docker-compose -f docker-compose-dev.yml ps

# Recriar banco de dados
python manage.py migrate --run-syncdb
```

### Erro de Permissões
```bash
# Verificar permissões do diretório
ls -la

# Corrigir permissões se necessário
chmod +x manage.py
```

## Suporte

Para suporte técnico:
- **Email**: felipe@aupi.com.br
- **Documentação**: Ver pasta `Documentacao/` para especificações detalhadas
- **Issues**: Reportar problemas no repositório Git

## Licença

Este projeto é propriedade da empresa e está sob licença restrita.