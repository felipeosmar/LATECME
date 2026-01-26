# LATECME - Sistema de Controle de Manufatura

Sistema Django para controle de manufatura aditiva de materiais metálicos, com foco em gestão de estoque de ligas metálicas, rastreamento de materiais, geração de códigos de barras.

## Funcionalidades Principais

### Gestão de Materiais
- Cadastro de materiais com códigos únicos
- Tipos suportados: Alumínio (AL), Titânio (TI), Aço Inox (SS), Inconel (IN), Cobalto-Cromo (CO)
- Controle de composição, densidade e certificações

### Controle de Estoque
- Itens de estoque com códigos de barras únicos
- Rastreamento de peso, lote do fornecedor, localização
- Fluxo de status: Registrado → Disponível → Reservado → Consumido
- Suporte a quarentena e descarte

### Gestão de Fornecedores
- Cadastro de fornecedores com informações de contato
- Controle de prazos de entrega
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
## Desenvolvimento

### Estrutura de Usuários
O sistema possui um modelo de usuário customizado com os seguintes perfis:
- **Operador**: Acesso ao estoque e movimentações
- **Administrador**: Acesso completo ao sistema
- **Comprador**: Acesso a compras e fornecedores
