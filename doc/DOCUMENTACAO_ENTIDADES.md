# Documentação das Entidades do Sistema LATECME

Sistema de Controle de Manufatura para Materiais de Manufatura Aditiva

## Sumário

1. [Visão Geral](#visão-geral)
2. [Modelos Base (Core)](#modelos-base-core)
3. [Autenticação e Usuários (Accounts)](#autenticação-e-usuários-accounts)
4. [Gestão de Materiais (Materials)](#gestão-de-materiais-materials)
5. [Controle de Estoque (Inventory)](#controle-de-estoque-inventory)
6. [Produção](#produção)
7. [Diagramas](#diagramas)

---

## Visão Geral

O LATECME é um sistema Django para controle de manufatura de materiais aditivos, especificamente projetado para gestão de inventário de ligas metálicas. O sistema possui **21 entidades** organizadas em **4 aplicativos**:

| App | Quantidade | Descrição |
|-----|------------|-----------|
| Core | 2 | Modelos base abstratos |
| Accounts | 2 | Autenticação e controle de acesso |
| Materials | 6 | Gestão de materiais e fornecedores |
| Inventory | 11 | Estoque e produção |

### Padrões de Design Utilizados

- **UUID Primary Keys**: Todas as entidades usam UUID ao invés de IDs sequenciais
- **Soft Delete**: Campo `is_active` permite exclusão lógica
- **Audit Trail**: Campos `created_by`, `updated_by`, `created_at`, `updated_at`
- **Multi-level Inheritance**: Hierarquia de modelos base reutilizáveis

---

## Modelos Base (Core)

Localização: `apps/core/models.py`

### TimeStampedModel (Abstrato)

Modelo base que fornece campos de timestamp automáticos.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `created_at` | DateTimeField | Data/hora de criação (automático) |
| `updated_at` | DateTimeField | Data/hora da última atualização (automático) |

### BaseModel (Abstrato)

Modelo base principal que herda de TimeStampedModel e adiciona auditoria completa.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUIDField | Identificador único (UUID v4) |
| `created_by` | ForeignKey → User | Usuário que criou o registro |
| `updated_by` | ForeignKey → User | Usuário que atualizou |
| `is_active` | BooleanField | Flag de soft delete (default: True) |

**Herança**: Todos os modelos de negócio herdam de BaseModel.

---

## Autenticação e Usuários (Accounts)

Localização: `apps/accounts/models.py`

### UserRole

Define as funções/papéis dos usuários no sistema.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `name` | CharField(50) | unique | Nome da função |
| `description` | TextField | blank | Descrição da função |
| `permissions` | JSONField | default=list | Lista de permissões em JSON |

**Meta**: ordering=['name'], verbose_name="Função"

### CustomUser

Modelo de usuário personalizado com workflow de aprovação.

**Herda de**: AbstractUser (Django)

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `status` | CharField(20) | choices | Status de aprovação |
| `role` | ForeignKey → UserRole | PROTECT, null | Função do usuário |
| `registration_date` | DateTimeField | auto_now_add | Data de registro |
| `approved_by` | ForeignKey → self | SET_NULL, null | Quem aprovou |
| `approved_at` | DateTimeField | null | Quando foi aprovado |
| `phone` | CharField(20) | blank | Telefone |
| `department` | CharField(100) | blank | Departamento |
| `profile_photo` | ImageField | null | Foto de perfil |

**Status possíveis**:
- `pending` - Aguardando Aprovação
- `approved` - Aprovado
- `rejected` - Rejeitado
- `suspended` - Suspenso

**Métodos principais**:
- `can_access_system()` → bool: Verifica se pode acessar (approved + role + is_active)
- `get_permissions()` → list: Retorna permissões da role

---

## Gestão de Materiais (Materials)

Localização: `apps/materials/models.py`

### ChemicalElement

Elementos químicos da tabela periódica para composição de materiais.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `symbol` | CharField(3) | unique | Símbolo (ex: Al, Ti, V) |
| `name` | CharField(50) | - | Nome completo |
| `atomic_number` | IntegerField | unique | Número atômico |
| `atomic_weight` | DecimalField(8,4) | - | Peso atômico (g/mol) |

### MaterialCategory

Categorização de materiais com cores visuais para UI.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `name` | CharField(100) | unique | Nome da categoria |
| `description` | TextField | blank | Descrição |
| `color` | CharField(7) | default=#007bff | Cor hexadecimal |

### Material

Definições dos materiais para manufatura aditiva.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `code` | CharField(20) | unique, regex | Código interno (ex: AL7075) |
| `name` | CharField(200) | - | Nome do material |
| `material_type` | CharField(10) | choices | Tipo do material |
| `density` | DecimalField(5,3) | 0.1-25.0 | Densidade (g/cm³) |
| `melting_point` | DecimalField(6,1) | null | Ponto de fusão (°C) |
| `specifications` | JSONField | default=dict | Especificações técnicas |
| `requires_certificate` | BooleanField | default=True | Requer certificado? |
| `storage_requirements` | TextField | blank | Requisitos de armazenamento |
| `safety_notes` | TextField | blank | Notas de segurança |
| `category` | ForeignKey → MaterialCategory | SET_NULL, null | Categoria |

**Tipos de Material** (`material_type`):
| Código | Descrição |
|--------|-----------|
| AL | Alumínio |
| TI | Titânio |
| SS | Aço Inoxidável |
| IN | Inconel |
| CO | Cobalto-Cromo |
| CU | Cobre |
| NI | Níquel |
| OTHER | Outros |

**Validação do código**: Deve seguir padrão `^[A-Z]{2,4}[A-Z0-9]+$`

**Métodos**:
- `get_main_suppliers()` → QuerySet: Top 3 fornecedores ativos por menor preço
- `get_best_price()` → Decimal: Menor preço disponível

### MaterialComposition

Composição química percentual dos materiais.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `material` | ForeignKey → Material | CASCADE | Material |
| `element` | ForeignKey → ChemicalElement | PROTECT | Elemento químico |
| `percentage` | DecimalField(5,2) | 0.01-100.00 | Porcentagem |
| `is_max` | BooleanField | default=False | É valor máximo? |

**Validação**: Soma das porcentagens não pode exceder 100%

**Constraint**: unique_together = ['material', 'element']

### Supplier

Fornecedores de materiais.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `name` | CharField(200) | - | Nome da empresa |
| `code` | CharField(50) | unique | Código interno |
| `cnpj` | CharField(18) | unique | CNPJ |
| `contact_email` | EmailField | - | Email de contato |
| `contact_phone` | CharField(20) | - | Telefone |
| `address` | TextField | blank | Endereço |
| `notes` | TextField | blank | Observações |

**Validação**: CNPJ deve ter exatamente 14 dígitos numéricos

### MaterialSupplier

Relacionamento Material-Fornecedor com informações de preço e prazo.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `material` | ForeignKey → Material | CASCADE | Material |
| `supplier` | ForeignKey → Supplier | CASCADE | Fornecedor |
| `supplier_code` | CharField(100) | - | Código do fornecedor |
| `price_per_kg` | DecimalField(10,2) | - | Preço (R$/kg) |
| `minimum_order` | DecimalField(10,3) | - | Pedido mínimo (kg) |
| `lead_time_days` | IntegerField | - | Prazo de entrega (dias) |
| `available` | BooleanField | default=True | Disponível? |
| `last_price_update` | DateTimeField | auto_now | Última atualização |
| `notes` | TextField | blank | Observações |

**Constraint**: unique_together = ['material', 'supplier']

**Método**: `calculate_total_cost(quantity_kg)` → Decimal ou None

---

## Controle de Estoque (Inventory)

Localização: `apps/inventory/models.py`

### Warehouse

Locais físicos de armazenamento.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `name` | CharField(100) | - | Nome do armazém |
| `code` | CharField(20) | unique | Código identificador |
| `description` | TextField | blank | Descrição |
| `location` | CharField(200) | - | Localização física |
| `manager` | ForeignKey → User | SET_NULL, null | Gerente responsável |

### MaterialStock

Níveis de estoque por material e armazém.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `material` | ForeignKey → Material | CASCADE | Material |
| `warehouse` | ForeignKey → Warehouse | CASCADE | Armazém |
| `current_quantity` | DecimalField(10,3) | min=0, default=0 | Quantidade atual (kg) |
| `reserved_quantity` | DecimalField(10,3) | min=0, default=0 | Quantidade reservada |
| `minimum_stock` | DecimalField(10,3) | default=0 | Estoque mínimo |
| `maximum_stock` | DecimalField(10,3) | null | Estoque máximo |
| `location_code` | CharField(50) | blank | Código da prateleira |
| `last_movement_date` | DateTimeField | null | Última movimentação |

**Constraint**: unique_together = ['material', 'warehouse']

**Propriedades**:
- `available_quantity` → Decimal: current_quantity - reserved_quantity
- `is_low_stock` → bool: current_quantity <= minimum_stock
- `is_out_of_stock` → bool: current_quantity <= 0

**Método**: `can_reserve(quantity)` → bool

### StockMovement

Registro de todas as movimentações de estoque.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `material` | ForeignKey → Material | CASCADE | Material |
| `warehouse` | ForeignKey → Warehouse | CASCADE | Armazém origem |
| `movement_type` | CharField(20) | choices | Tipo de movimento |
| `reason` | CharField(50) | choices | Razão do movimento |
| `quantity` | DecimalField(10,3) | min=0.001 | Quantidade (kg) |
| `unit_cost` | DecimalField(10,2) | null | Custo unitário (R$/kg) |
| `total_cost` | DecimalField(12,2) | null | Custo total |
| `batch_number` | CharField(100) | blank | Número do lote |
| `expiry_date` | DateField | null | Data de validade |
| `certificate_number` | CharField(100) | blank | Número do certificado |
| `reference_document` | CharField(100) | blank | Documento referência |
| `notes` | TextField | blank | Observações |
| `user` | ForeignKey → User | SET_NULL, null | Usuário responsável |
| `destination_warehouse` | ForeignKey → Warehouse | SET_NULL, null | Armazém destino |

**Tipos de Movimento** (`movement_type`):
| Código | Descrição |
|--------|-----------|
| IN | Entrada |
| OUT | Saída |
| TRANSFER | Transferência |
| ADJUSTMENT | Ajuste |
| RETURN | Devolução |
| LOSS | Perda |

**Razões** (`reason`):
PURCHASE, PRODUCTION, SALE, INTERNAL_USE, TRANSFER, INVENTORY_ADJUSTMENT, EXPIRED, DAMAGED, LOST, RETURN, OTHER

**Lógica de negócio**: `save()` atualiza automaticamente MaterialStock

### StockReservation

Reservas temporárias de estoque.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `material` | ForeignKey → Material | CASCADE | Material |
| `warehouse` | ForeignKey → Warehouse | CASCADE | Armazém |
| `quantity` | DecimalField(10,3) | min=0.001 | Quantidade (kg) |
| `reserved_by` | ForeignKey → User | CASCADE | Quem reservou |
| `reservation_date` | DateTimeField | auto_now_add | Data da reserva |
| `expiry_date` | DateTimeField | - | Expiração da reserva |
| `purpose` | CharField(200) | - | Finalidade |
| `reference_document` | CharField(100) | blank | Documento referência |
| `notes` | TextField | blank | Observações |

**Propriedade**: `is_expired` → bool

**Lógica**: Atualiza `reserved_quantity` em MaterialStock automaticamente

### InventoryCount

Sessões de contagem física de inventário.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `reference_number` | CharField(50) | unique | Número de referência (auto) |
| `warehouse` | ForeignKey → Warehouse | CASCADE | Armazém |
| `count_date` | DateField | - | Data da contagem |
| `status` | CharField(20) | choices | Status da contagem |
| `counter` | ForeignKey → User | SET_NULL, null | Contador |
| `supervisor` | ForeignKey → User | SET_NULL, null | Supervisor |
| `notes` | TextField | blank | Observações |

**Status**: PLANNED, IN_PROGRESS, COMPLETED, CANCELLED

**Formato do número**: `INV-{WAREHOUSE_CODE}-{YYYYMMDD}-{NNN}`

### InventoryCountItem

Itens individuais de uma contagem de inventário.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `inventory_count` | ForeignKey → InventoryCount | CASCADE | Contagem |
| `material` | ForeignKey → Material | CASCADE | Material |
| `system_quantity` | DecimalField(10,3) | - | Quantidade sistema |
| `counted_quantity` | DecimalField(10,3) | null | Quantidade contada |
| `location_code` | CharField(50) | blank | Localização |
| `notes` | TextField | blank | Observações |

**Constraint**: unique_together = ['inventory_count', 'material']

**Propriedades**:
- `variance` → Decimal: counted_quantity - system_quantity
- `variance_percentage` → Decimal: porcentagem de variação

---

## Produção

### ProductionOrder

Ordens de produção.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `order_number` | CharField(50) | unique | Número da ordem (auto) |
| `material` | ForeignKey → Material | PROTECT | Material a produzir |
| `planned_quantity` | DecimalField(10,3) | min=0.001 | Quantidade planejada |
| `produced_quantity` | DecimalField(10,3) | default=0 | Quantidade produzida |
| `status` | CharField(20) | choices | Status |
| `planned_start_date` | DateField | null | Data início planejada |
| `planned_end_date` | DateField | null | Data fim planejada |
| `actual_start_date` | DateTimeField | null | Início real |
| `actual_end_date` | DateTimeField | null | Fim real |
| `responsible` | ForeignKey → User | SET_NULL, null | Responsável |
| `notes` | TextField | blank | Observações |

**Status**: DRAFT, PLANNED, IN_PROGRESS, COMPLETED, CANCELLED

**Formato do número**: `OP-{YYYYMMDD}-{NNN}`

**Métodos**:
- `can_start()` → bool
- `start(user)` → Inicia produção
- `complete(user)` → Finaliza produção

**Propriedades**:
- `completion_percentage` → Decimal
- `is_overdue` → bool

### Bin (Contentor)

Recipientes de armazenamento de materiais.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `code` | CharField(50) | - | Código do contentor |
| `warehouse` | ForeignKey → Warehouse | CASCADE | Armazém |
| `status` | CharField(20) | choices | Status |
| `capacity` | DecimalField(10,3) | null, min=0.001 | Capacidade (kg) |
| `current_material` | ForeignKey → Material | SET_NULL, null | Material atual |
| `current_quantity` | DecimalField(10,3) | default=0 | Quantidade atual |
| `current_supplier_batch` | CharField(100) | blank | Lote fornecedor |
| `current_certificate` | CharField(100) | blank | Certificado |
| `location_code` | CharField(50) | blank | Localização |
| `notes` | TextField | blank | Observações |

**Status**: EMPTY, LOADED, IN_USE, MAINTENANCE

**Constraint**: unique_together = ['warehouse', 'code']

**Propriedades**:
- `is_empty` → bool
- `is_loaded` → bool

**Métodos**:
- `load_material(material, quantity, ...)` → Carrega material
- `unload_material(quantity, ...)` → Descarrega material
- `empty(user, notes)` → Esvazia completamente

### Batch (Batelada)

Lotes de produção coletados de múltiplos contentores.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `batch_number` | CharField(50) | unique | Número da batelada (auto) |
| `production_order` | ForeignKey → ProductionOrder | PROTECT | Ordem de produção |
| `material` | ForeignKey → Material | PROTECT | Material |
| `status` | CharField(20) | choices | Status |
| `target_quantity` | DecimalField(10,3) | min=0.001 | Quantidade alvo |
| `actual_quantity` | DecimalField(10,3) | default=0 | Quantidade real |
| `prepared_by` | ForeignKey → User | SET_NULL, null | Preparado por |
| `preparation_date` | DateTimeField | null | Data preparação |
| `production_start_date` | DateTimeField | null | Início produção |
| `completion_date` | DateTimeField | null | Conclusão |
| `notes` | TextField | blank | Observações |

**Status**: PREPARATION, READY, IN_PRODUCTION, COMPLETED, CANCELLED

**Formato do número**: `BAT-{YYYYMMDD}-{NNN}`

**Métodos**:
- `add_bin_material(bin, quantity, user)` → Adiciona material de um contentor
- `mark_ready(user)` → Marca como pronto
- `start_production(user)` → Inicia produção
- `complete(user)` → Finaliza

**Propriedades**:
- `quantity_variance` → Decimal
- `is_complete` → bool

### BatchItem

Itens individuais coletados para uma batelada.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `batch` | ForeignKey → Batch | CASCADE | Batelada |
| `bin` | ForeignKey → Bin | SET_NULL, null | Contentor origem |
| `material` | ForeignKey → Material | PROTECT | Material |
| `quantity` | DecimalField(10,3) | min=0.001 | Quantidade (kg) |
| `supplier_batch` | CharField(100) | blank | Lote fornecedor |
| `certificate` | CharField(100) | blank | Certificado |
| `collected_by` | ForeignKey → User | SET_NULL, null | Coletado por |
| `collected_at` | DateTimeField | auto_now_add | Data coleta |
| `notes` | TextField | blank | Observações |

### BinHistory

Histórico de movimentações dos contentores.

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| `bin` | ForeignKey → Bin | CASCADE | Contentor |
| `movement_type` | CharField(20) | choices | Tipo movimento |
| `material` | ForeignKey → Material | PROTECT | Material |
| `quantity` | DecimalField(10,3) | min=0.001 | Quantidade |
| `quantity_before` | DecimalField(10,3) | default=0 | Quantidade antes |
| `quantity_after` | DecimalField(10,3) | default=0 | Quantidade depois |
| `supplier_batch` | CharField(100) | blank | Lote fornecedor |
| `certificate` | CharField(100) | blank | Certificado |
| `batch` | ForeignKey → Batch | SET_NULL, null | Batelada relacionada |
| `performed_by` | ForeignKey → User | SET_NULL, null | Executado por |
| `notes` | TextField | blank | Observações |

**Tipos**: IN, OUT, EMPTY, TRANSFER, ADJUSTMENT

---

## Diagramas

Os diagramas de relacionamento estão disponíveis nos seguintes arquivos Excalidraw:

1. **[Modelos Base](./diagrams/core-models.excalidraw)** - Hierarquia de herança dos modelos
2. **[Módulo Accounts](./diagrams/accounts-models.excalidraw)** - Autenticação e usuários
3. **[Módulo Materials](./diagrams/materials-models.excalidraw)** - Gestão de materiais
4. **[Módulo Inventory](./diagrams/inventory-models.excalidraw)** - Estoque e produção
5. **[Visão Geral](./diagrams/overview.excalidraw)** - Relacionamentos entre módulos

---

## Fluxos de Negócio Principais

### 1. Workflow de Aprovação de Usuário
```
Registro → status: pending
    ↓
Admin aprova → status: approved, approved_by, approved_at
    ↓
Usuário pode acessar sistema (can_access_system = True)
```

### 2. Fluxo de Movimentação de Estoque
```
StockMovement criado
    ↓
save() → update_stock()
    ↓
MaterialStock atualizado automaticamente
```

### 3. Fluxo de Produção
```
ProductionOrder (DRAFT)
    ↓ start()
ProductionOrder (IN_PROGRESS)
    ↓
Batch criado (PREPARATION)
    ↓ add_bin_material()
Material coletado de Bins → BatchItem criado → BinHistory registrado
    ↓ mark_ready()
Batch (READY)
    ↓ start_production()
Batch (IN_PRODUCTION)
    ↓ complete()
Batch (COMPLETED) → ProductionOrder.produced_quantity atualizado
```

### 4. Fluxo de Contagem de Inventário
```
InventoryCount (PLANNED)
    ↓
InventoryCountItem criados com system_quantity
    ↓
Contagem física → counted_quantity preenchido
    ↓
variance calculado automaticamente
```
