# Purchasing Views - Estrutura Modular

Este diretório contém os views do módulo de Compras (Purchasing), organizados por domínio funcional.

## 📋 Visão Geral

Anteriormente, todos os views de compras estavam em um único arquivo `views.py` com **1084 linhas**. Para melhorar a manutenibilidade e seguir o princípio de responsabilidade única, o código foi dividido em **5 módulos especializados** com base nos domínios de negócio.

## 🗂️ Estrutura de Módulos

### `dashboard.py` - Dashboard Principal
**1 view** | Visão geral do módulo de compras

- `dashboard` - Dashboard com estatísticas de solicitações, pedidos e recebimentos

**URL:** `/purchasing/`

---

### `purchase_requests.py` - Solicitações de Compra
**9 views** | Gerenciamento completo de solicitações (requisições)

#### CRUD Básico
- `request_list` - Lista de solicitações com filtros
- `request_detail` - Detalhes de uma solicitação
- `request_create` - Criar nova solicitação
- `request_update` - Editar solicitação em rascunho

#### Workflow de Aprovação
- `request_submit` - Submeter solicitação para aprovação
- `request_approve` - Aprovar solicitação
- `request_reject` - Rejeitar solicitação

#### Gerenciamento de Itens
- `request_item_add` - Adicionar item à solicitação
- `request_item_remove` - Remover item da solicitação

**URLs Base:** `/purchasing/requests/`

---

### `purchase_orders.py` - Pedidos de Compra
**7 views** | Gerenciamento de pedidos aos fornecedores

#### CRUD Básico
- `order_list` - Lista de pedidos de compra
- `order_detail` - Detalhes de um pedido
- `order_create` - Criar pedido a partir de solicitações aprovadas

#### Workflow de Pedidos
- `order_send` - Enviar pedido ao fornecedor
- `order_confirm` - Confirmar recebimento do pedido pelo fornecedor

#### Gerenciamento de Itens
- `order_item_add` - Adicionar item ao pedido
- `order_item_remove` - Remover item do pedido

**URLs Base:** `/purchasing/orders/`

---

### `receiving.py` - Recebimento de Materiais
**6 views** | Gerenciamento de recebimentos físicos

#### CRUD Básico
- `receiving_list` - Lista de recebimentos
- `receiving_detail` - Detalhes de um recebimento
- `receiving_create` - Registrar novo recebimento

#### Workflow de Aprovação
- `receiving_approve` - Aprovar recebimento (atualiza estoque)
- `receiving_reject` - Rejeitar recebimento

#### Gerenciamento de Itens
- `receiving_item_add` - Adicionar item ao recebimento

**URLs Base:** `/purchasing/receivings/`

---

### `api.py` - Endpoints de API
**2 views** | Endpoints JSON para integrações

- `api_approved_requests` - Lista de solicitações aprovadas (JSON)
- `api_order_items` - Lista de itens de pedido (JSON)

**URLs Base:** `/purchasing/api/`

---

## 📊 Resumo Estatístico

| Módulo | Views | Linhas de Código | Responsabilidade |
|--------|-------|------------------|------------------|
| `dashboard.py` | 1 | ~50 | Dashboard e estatísticas |
| `purchase_requests.py` | 9 | ~420 | Ciclo completo de solicitações |
| `purchase_orders.py` | 7 | ~310 | Ciclo completo de pedidos |
| `receiving.py` | 6 | ~345 | Ciclo completo de recebimentos |
| `api.py` | 2 | ~80 | Endpoints de integração |
| **TOTAL** | **25** | **~1207** | - |

## 🔄 Fluxo de Trabalho (Workflow)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PURCHASING WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

1️⃣ SOLICITAÇÃO (Purchase Request)
   └─> [DRAFT] ──submit──> [PENDING] ──approve/reject──> [APPROVED/REJECTED]
                                                               │
2️⃣ PEDIDO (Purchase Order)                                     │
   └─> [DRAFT] <──create from approved requests───────────────┘
        │
        └──send──> [SENT] ──confirm──> [CONFIRMED]
                                            │
3️⃣ RECEBIMENTO (Receiving)                 │
   └─> [DRAFT] <──create from order────────┘
        │
        └──approve──> [RECEIVED] ──> [Atualiza Estoque]
```

## 🎯 Padrões Implementados

### Decoradores Utilizados
- `@login_required` - Todos os views requerem autenticação
- `@require_http_methods(['GET', 'POST'])` - Controle de métodos HTTP

### Tratamento de Erros
- Validações de permissão por status
- Mensagens de erro amigáveis via `messages.error()`
- Redirecionamentos apropriados em caso de erro

### Templates
Cada view renderiza templates específicos localizados em:
- `purchasing/dashboard.html`
- `purchasing/request_*.html`
- `purchasing/order_*.html`
- `purchasing/receiving_*.html`

### Modelos Utilizados
- `PurchaseRequest` + `PurchaseRequestItem`
- `PurchaseOrder` + `PurchaseOrderItem`
- `Receiving` + `ReceivingItem`

## 📦 Importação de Views

Todos os views estão exportados no `__init__.py` do package e podem ser importados de duas formas:

```python
# Forma 1: Import direto do package
from apps.purchasing.views import dashboard, request_list, order_create

# Forma 2: Import do módulo específico
from apps.purchasing.views.purchase_requests import request_approve
from apps.purchasing.views.purchase_orders import order_send
from apps.purchasing.views.receiving import receiving_approve
```

## 🔗 URLs

Todas as URLs são configuradas em `apps/purchasing/urls.py`:

```python
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Purchase Requests
    path('requests/', views.request_list, name='request_list'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    # ... (25 URLs total)
]
```

## ✅ Benefícios da Refatoração

### Antes (views.py monolítico)
- ❌ **1084 linhas** em um único arquivo
- ❌ Difícil de navegar e encontrar código específico
- ❌ Múltiplos domínios misturados
- ❌ Alto risco de conflitos em merge
- ❌ Violação do Single Responsibility Principle

### Depois (estrutura modular)
- ✅ **5 módulos** com responsabilidades claras
- ✅ **~240 linhas** por módulo em média
- ✅ Fácil localização de código por domínio
- ✅ Menor risco de conflitos
- ✅ Preparado para crescimento (ex: Supplier Search API)
- ✅ Melhor testabilidade e manutenibilidade

## 🔍 Como Encontrar um View

1. **Por funcionalidade:**
   - Solicitações → `purchase_requests.py`
   - Pedidos → `purchase_orders.py`
   - Recebimentos → `receiving.py`
   - APIs → `api.py`
   - Dashboard → `dashboard.py`

2. **Por nome da URL:** Verifique `urls.py` e veja qual view está mapeado

3. **Por template:** Busque o nome do template no módulo correspondente

## 🚀 Próximos Passos

Esta estrutura está preparada para futuras melhorias, como:
- Adicionar endpoint de busca de fornecedores (`api.py`)
- Implementar workflow de cotações (`purchase_orders.py`)
- Adicionar relatórios especializados (novo módulo `reports.py`)
- Migrar lógica complexa para services (seguir padrão DDD)

## 📝 Notas de Migração

**Data da Refatoração:** 2026-01-28

- ✅ Todos os 25 views foram migrados sem alteração de funcionalidade
- ✅ URLs continuam idênticas (compatibilidade mantida)
- ✅ Imports foram atualizados automaticamente via `__init__.py`
- ✅ Verificação completa via Django system checks
- ✅ Arquivo original `views.py` foi removido após validação

---

**Mantido por:** Equipe LATECME
**Última atualização:** 2026-01-28
