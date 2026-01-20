# Documentação de Software - Sistema de Manufatura Aditiva

## 1. Diagrama de Entidade Relacionamento (DER)

```mermaid
erDiagram
    User ||--o{ Material : creates
    User ||--o{ StockItem : creates
    User ||--o{ PurchaseOrder : creates
    User ||--o{ StockMovement : registers
    
    Supplier ||--o{ MaterialSupplier : supplies
    Material ||--o{ MaterialSupplier : has_suppliers
    Material ||--o{ StockItem : is_type_of
    
    MaterialSupplier {
        uuid id PK
        uuid material_id FK
        uuid supplier_id FK
        string supplier_code
        decimal price_per_kg
        decimal minimum_order
        int lead_time_days
        datetime created_at
        datetime updated_at
    }
    
    Material {
        uuid id PK
        string code UK
        string name
        string material_type
        json composition
        decimal density
        json specifications
        boolean requires_certificate
        boolean is_active
        uuid created_by FK
        uuid updated_by FK
        datetime created_at
        datetime updated_at
    }
    
    Supplier {
        uuid id PK
        string code UK
        string name
        string cnpj UK
        string contact_email
        string contact_phone
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    StockItem {
        uuid id PK
        string unique_code UK
        uuid material_id FK
        decimal weight
        string supplier_batch
        datetime entry_date
        string location
        string status
        uuid purchase_order_id FK
        json metadata
        uuid created_by FK
        datetime created_at
    }
    
    StockMovement {
        uuid id PK
        uuid stock_item_id FK
        string movement_type
        decimal quantity
        string production_order
        string notes
        uuid user_id FK
        datetime timestamp
    }
    
    PurchaseOrder {
        uuid id PK
        string order_number UK
        uuid supplier_id FK
        datetime order_date
        datetime expected_date
        string status
        decimal total_value
        json items
        uuid created_by FK
        datetime created_at
        datetime updated_at
    }
    
    PurchaseOrderItem {
        uuid id PK
        uuid purchase_order_id FK
        uuid material_id FK
        decimal quantity
        decimal unit_price
        json specifications
        datetime created_at
    }
    
    LabelPrintJob {
        uuid id PK
        string unique_code FK
        string status
        json label_data
        datetime requested_at
        datetime printed_at
        string error_message
        uuid requested_by FK
    }
    
    User {
        int id PK
        string username UK
        string email UK
        string first_name
        string last_name
        boolean is_active
        boolean is_staff
        datetime date_joined
    }
    
    Supplier ||--o{ PurchaseOrder : receives
    PurchaseOrder ||--o{ PurchaseOrderItem : contains
    Material ||--o{ PurchaseOrderItem : ordered_in
    StockItem ||--o{ StockMovement : has_movements
    PurchaseOrder ||--o{ StockItem : generates
    StockItem ||--|| LabelPrintJob : has_print_job
```

## 2. Diagramas de Sequência

### 2.1 Fluxo de Entrada de Material

```mermaid
sequenceDiagram
    participant O as Operador
    participant W as Web Interface
    participant API as Django API
    participant S as StockService
    participant C as Celery
    participant P as Printer
    participant DB as PostgreSQL
    participant R as Redis Cache
    
    O->>W: Acessa tela de entrada
    W->>API: GET /api/v1/materials/
    API->>DB: Query materiais ativos
    DB-->>API: Lista de materiais
    API-->>W: JSON response
    W-->>O: Exibe formulário
    
    O->>W: Preenche dados entrada
    Note over O,W: Material, peso, lote, localização
    
    W->>API: POST /api/v1/inventory/entry
    API->>API: Valida dados (DRF Serializer)
    
    alt Dados inválidos
        API-->>W: Erro 422 (detalhes)
        W-->>O: Exibe erros
    else Dados válidos
        API->>S: create_stock_entry()
        S->>S: generate_unique_code()
        S->>DB: BEGIN TRANSACTION
        S->>DB: INSERT stock_item
        S->>DB: INSERT stock_movement
        S->>DB: UPDATE material_stock_summary
        S->>DB: COMMIT
        
        S->>C: print_label_task.delay()
        C->>R: Adiciona tarefa na fila
        S-->>API: StockItem created
        API-->>W: 201 Created + dados
        W-->>O: Sucesso + código único
        
        Note over C,P: Processo assíncrono
        C->>R: Pega tarefa da fila
        C->>P: Conecta impressora
        C->>P: Envia dados etiqueta
        P-->>C: Status impressão
        C->>DB: UPDATE label_print_job
        C->>R: Notifica conclusão
    end
```

### 2.2 Fluxo de Saída de Material

```mermaid
sequenceDiagram
    participant O as Operador
    participant S as Scanner
    participant W as Web Interface
    participant API as Django API
    participant IS as InventoryService
    participant DB as PostgreSQL
    participant C as Cache
    
    O->>S: Escaneia código de barras
    S->>W: Envia código
    W->>API: GET /api/v1/inventory/items/{code}
    
    API->>C: Verifica cache
    alt Cache hit
        C-->>API: Dados do item
    else Cache miss
        API->>DB: SELECT stock_item
        DB-->>API: Dados do item
        API->>C: Armazena em cache
    end
    
    API-->>W: Detalhes do item
    W-->>O: Exibe informações
    
    alt Item disponível
        O->>W: Confirma saída + qtd
        W->>API: POST /api/v1/inventory/movement
        API->>IS: register_movement()
        IS->>DB: BEGIN TRANSACTION
        IS->>DB: INSERT stock_movement
        IS->>DB: UPDATE stock_item status
        IS->>DB: UPDATE material_stock_summary
        IS->>DB: COMMIT
        IS->>C: Invalida cache
        IS-->>API: Movement registered
        API-->>W: 201 Created
        W-->>O: Saída registrada
    else Item indisponível
        W-->>O: Item já consumido/reservado
    end
```

### 2.3 Fluxo de Impressão de Etiqueta

```mermaid
sequenceDiagram
    participant API as Django API
    participant C as Celery Worker
    participant Q as Redis Queue
    participant PS as PrinterService
    participant P as Physical Printer
    participant DB as PostgreSQL
    
    API->>Q: Adiciona tarefa print_label
    API-->>API: Retorna ID da tarefa
    
    C->>Q: Poll por novas tarefas
    Q-->>C: Tarefa print_label
    
    C->>DB: Busca dados do item
    DB-->>C: Dados completos
    
    C->>PS: prepare_label_data()
    PS->>PS: Formata dados
    PS->>PS: Gera código de barras
    PS-->>C: Label data pronto
    
    C->>PS: connect_printer()
    
    alt Impressora disponível
        PS->>P: Verifica status
        P-->>PS: Status OK
        
        PS->>P: Envia comando ESC/POS
        Note over PS,P: Código de barras, texto, formatação
        
        P-->>PS: Confirmação impressão
        PS-->>C: Sucesso
        
        C->>DB: UPDATE label_print_job
        Note over C,DB: status='completed', printed_at=now()
        
    else Impressora indisponível
        PS-->>C: Erro conexão
        C->>C: Retry (max 3x)
        
        alt Retry bem-sucedido
            C->>PS: Nova tentativa
        else Falha após retries
            C->>DB: UPDATE label_print_job
            Note over C,DB: status='failed', error_message
            C->>Q: Envia para DLQ
        end
    end
```

## 3. Diagrama de Classes

### 3.1 Camada de Modelos (Django Models)

```mermaid
classDiagram
    class BaseModel {
        <<abstract>>
        +UUID id
        +DateTime created_at
        +DateTime updated_at
        +User created_by
        +User updated_by
        +Boolean is_active
        +save()
        +delete()
    }
    
    class Material {
        +String code
        +String name
        +String material_type
        +JSON composition
        +Decimal density
        +JSON specifications
        +Boolean requires_certificate
        +get_available_stock() Decimal
        +get_suppliers() QuerySet
        +validate_code() Boolean
    }
    
    class Supplier {
        +String code
        +String name
        +String cnpj
        +String contact_email
        +String contact_phone
        +get_materials() QuerySet
        +get_active_orders() QuerySet
    }
    
    class MaterialSupplier {
        +Material material
        +Supplier supplier
        +String supplier_code
        +Decimal price_per_kg
        +Decimal minimum_order
        +Integer lead_time_days
        +calculate_order_cost(quantity) Decimal
    }
    
    class StockItem {
        +String unique_code
        +Material material
        +Decimal weight
        +String supplier_batch
        +DateTime entry_date
        +String location
        +String status
        +PurchaseOrder purchase_order
        +JSON metadata
        +generate_unique_code() String
        +is_available() Boolean
        +reserve() Boolean
        +consume() Boolean
    }
    
    class StockMovement {
        +StockItem stock_item
        +String movement_type
        +Decimal quantity
        +String production_order
        +String notes
        +User user
        +DateTime timestamp
        +validate_movement() Boolean
        +get_balance_after() Decimal
    }
    
    class PurchaseOrder {
        +String order_number
        +Supplier supplier
        +DateTime order_date
        +DateTime expected_date
        +String status
        +Decimal total_value
        +generate_order_number() String
        +add_item(material, quantity, price)
        +receive_partial(items)
        +receive_complete()
        +cancel()
    }
    
    BaseModel <|-- Material
    BaseModel <|-- Supplier
    BaseModel <|-- MaterialSupplier
    BaseModel <|-- StockItem
    BaseModel <|-- StockMovement
    BaseModel <|-- PurchaseOrder
    
    Material "1" -- "*" MaterialSupplier
    Supplier "1" -- "*" MaterialSupplier
    Material "1" -- "*" StockItem
    StockItem "1" -- "*" StockMovement
    Supplier "1" -- "*" PurchaseOrder
    PurchaseOrder "1" -- "*" StockItem
```

### 3.2 Camada de Serviços

```mermaid
classDiagram
    class BaseService {
        <<abstract>>
        +Model model
        +get_by_id(id) Model
        +get_all(filters) QuerySet
        +create(data) Model
        +update(id, data) Model
        +delete(id) Boolean
    }
    
    class StockService {
        +generate_unique_code() String
        +create_entry(material_id, weight, batch, location) StockItem
        +register_movement(item_id, type, quantity, order) StockMovement
        +check_availability(material_id) Dict
        +get_stock_by_location(location) QuerySet
        +reserve_stock(item_id, quantity) Boolean
        +consume_stock(item_id, quantity, order) Boolean
    }
    
    class IdentificationService {
        +generate_code(prefix) String
        +validate_code(code) Boolean
        +decode_barcode(image_data) String
        +get_next_sequence(prefix) Integer
        +format_barcode(code) String
    }
    
    class PrinterService {
        +connect() Boolean
        +disconnect() Boolean
        +print_label(data) Boolean
        +print_barcode(code, text) Boolean
        +check_status() Dict
        +get_queue_size() Integer
    }
    
    class BarcodeReaderService {
        +connect(port) Boolean
        +disconnect() Boolean
        +read_sync() String
        +read_async(callback) None
        +start_continuous_read() None
        +stop_continuous_read() None
    }
    
    class MaterialService {
        +create_material(data) Material
        +update_material(id, data) Material
        +add_supplier(material_id, supplier_id, price_data) MaterialSupplier
        +get_by_type(material_type) QuerySet
        +search_by_composition(element, min_percent) QuerySet
    }
    
    BaseService <|-- StockService
    BaseService <|-- MaterialService
    StockService ..> IdentificationService : uses
    StockService ..> PrinterService : uses
```

### 3.3 Camada de API (Django REST Framework)

```mermaid
classDiagram
    class BaseViewSet {
        <<abstract>>
        +queryset
        +serializer_class
        +permission_classes
        +filter_backends
        +list(request) Response
        +create(request) Response
        +retrieve(request, pk) Response
        +update(request, pk) Response
        +destroy(request, pk) Response
    }
    
    class MaterialViewSet {
        +queryset: Material.objects
        +serializer_class: MaterialSerializer
        +filterset_class: MaterialFilter
        +check_availability(request, pk) Response
        +suppliers(request, pk) Response
        +price_history(request, pk) Response
    }
    
    class StockItemViewSet {
        +queryset: StockItem.objects
        +serializer_class: StockItemSerializer
        +create_entry(request) Response
        +register_movement(request) Response
        +scan_barcode(request) Response
        +print_label(request, pk) Response
        +bulk_entry(request) Response
    }
    
    class BaseSerializer {
        <<abstract>>
        +validate(attrs) Dict
        +create(validated_data) Model
        +update(instance, validated_data) Model
    }
    
    class MaterialSerializer {
        +fields: [id, code, name, type, density]
        +validate_code(value) String
        +validate_density(value) Decimal
    }
    
    class StockItemSerializer {
        +fields: [id, unique_code, material, weight, status]
        +material: MaterialSerializer
        +validate_weight(value) Decimal
        +validate_status(value) String
    }
    
    class StockMovementSerializer {
        +fields: [stock_item, type, quantity, timestamp]
        +validate_quantity(value) Decimal
        +validate_movement_type(value) String
        +validate(attrs) Dict
    }
    
    BaseViewSet <|-- MaterialViewSet
    BaseViewSet <|-- StockItemViewSet
    
    BaseSerializer <|-- MaterialSerializer
    BaseSerializer <|-- StockItemSerializer
    BaseSerializer <|-- StockMovementSerializer
    
    MaterialViewSet ..> MaterialSerializer : uses
    StockItemViewSet ..> StockItemSerializer : uses
    StockItemViewSet ..> StockMovementSerializer : uses
```

### 3.4 Camada de Tarefas Assíncronas (Celery)

```mermaid
classDiagram
    class BaseTask {
        <<abstract>>
        +String name
        +Integer max_retries
        +Integer default_retry_delay
        +run(*args, **kwargs)
        +retry(exc, countdown)
        +on_success(retval, task_id, args, kwargs)
        +on_failure(exc, task_id, args, kwargs)
    }
    
    class PrintLabelTask {
        +name: "hardware.print_label"
        +max_retries: 3
        +run(unique_code, label_data) Dict
        +handle_printer_error(error) None
    }
    
    class BarcodeReadTask {
        +name: "hardware.read_barcode"
        +run(device_id) String
        +broadcast_result(code) None
    }
    
    class StockReportTask {
        +name: "inventory.generate_report"
        +run(report_type, filters) String
        +send_email(report_path, recipients) None
    }
    
    class MaterialAlertTask {
        +name: "inventory.check_minimum_stock"
        +run() Dict
        +check_all_materials() List
        +send_alerts(low_stock_items) None
    }
    
    class DataImportTask {
        +name: "purchasing.import_orders"
        +run(file_path) Dict
        +validate_file(path) Boolean
        +process_row(row) Dict
    }
    
    BaseTask <|-- PrintLabelTask
    BaseTask <|-- BarcodeReadTask
    BaseTask <|-- StockReportTask
    BaseTask <|-- MaterialAlertTask
    BaseTask <|-- DataImportTask
    
    PrintLabelTask ..> PrinterService : uses
    BarcodeReadTask ..> BarcodeReaderService : uses
    StockReportTask ..> StockService : uses
    MaterialAlertTask ..> MaterialService : uses
```

## 4. Diagrama de Componentes

```mermaid
graph TB
    subgraph "Frontend Layer"
        WEB[Web Interface<br/>React/Vue.js]
        MOBILE[Mobile App<br/>React Native]
    end
    
    subgraph "API Gateway"
        NGINX[Nginx<br/>Load Balancer]
    end
    
    subgraph "Application Layer"
        DJANGO[Django Application]
        DRF[Django REST Framework]
        ADMIN[Django Admin]
        
        subgraph "Django Apps"
            MATERIALS[Materials App]
            INVENTORY[Inventory App]
            IDENTIFICATION[Identification App]
            PURCHASING[Purchasing App]
            HARDWARE[Hardware App]
        end
    end
    
    subgraph "Task Queue Layer"
        CELERY[Celery Workers]
        BEAT[Celery Beat]
        FLOWER[Flower Monitor]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL<br/>Main Database)]
        REDIS[(Redis<br/>Cache & Queue)]
    end
    
    subgraph "Hardware Layer"
        PRINTER[Label Printer<br/>USB/Serial]
        SCANNER[Barcode Scanner<br/>USB/Serial]
    end
    
    WEB --> NGINX
    MOBILE --> NGINX
    NGINX --> DJANGO
    DJANGO --> DRF
    DJANGO --> ADMIN
    
    DRF --> MATERIALS
    DRF --> INVENTORY
    DRF --> IDENTIFICATION
    DRF --> PURCHASING
    
    INVENTORY --> CELERY
    IDENTIFICATION --> CELERY
    
    CELERY --> REDIS
    BEAT --> REDIS
    CELERY --> HARDWARE
    
    DJANGO --> POSTGRES
    DJANGO --> REDIS
    
    HARDWARE --> PRINTER
    HARDWARE --> SCANNER
    
    FLOWER --> CELERY
```

## 5. Diagrama de Estados - Ciclo de Vida do Item de Estoque

```mermaid
stateDiagram-v2
    [*] --> Registrado: Entrada no sistema
    
    Registrado --> Disponível: Etiqueta impressa
    Registrado --> Falha_Impressão: Erro na impressora
    
    Falha_Impressão --> Disponível: Reimpressão bem-sucedida
    
    Disponível --> Reservado: Alocado para produção
    Disponível --> Em_Quarentena: Problema detectado
    
    Reservado --> Disponível: Reserva cancelada
    Reservado --> Consumido: Usado na produção
    
    Em_Quarentena --> Disponível: Liberado após análise
    Em_Quarentena --> Descartado: Reprovado
    
    Consumido --> [*]: Fim do ciclo
    Descartado --> [*]: Fim do ciclo
    
    note right of Disponível
        Estado padrão para
        materiais em estoque
    end note
    
    note right of Reservado
        Material alocado mas
        ainda não utilizado
    end note
```

## 6. Diagrama de Atividades - Processo de Entrada de Material

```mermaid
graph TD
    A[Início] --> B[Receber Material]
    B --> C{Material<br/>Cadastrado?}
    
    C -->|Não| D[Cadastrar Material]
    D --> E[Definir Fornecedores]
    E --> F
    
    C -->|Sim| F[Pesar Material]
    F --> G[Inserir Dados no Sistema]
    
    G --> H{Dados<br/>Válidos?}
    H -->|Não| I[Exibir Erros]
    I --> G
    
    H -->|Sim| J[Gerar Código Único]
    J --> K[Salvar no Banco]
    K --> L[Enviar para Impressão]
    
    L --> M{Impressão<br/>OK?}
    M -->|Não| N[Tentar Novamente]
    N --> O{Máx<br/>Tentativas?}
    O -->|Não| L
    O -->|Sim| P[Notificar Erro]
    
    M -->|Sim| Q[Colar Etiqueta]
    Q --> R[Alocar em Localização]
    R --> S[Atualizar Status]
    S --> T[Fim]
    
    P --> T
```

## 7. Notas de Implementação

### 7.1 Padrões de Código
- **Models**: Usar validators do Django para regras de negócio
- **Services**: Lógica de negócio isolada dos models
- **Serializers**: Validação de entrada/saída da API
- **Tasks**: Operações assíncronas e que podem falhar

### 7.2 Segurança
- Todas as operações autenticadas via JWT
- Auditoria em todas as tabelas (created_by, updated_by)
- Soft delete para manter histórico
- Backup diário do PostgreSQL

### 7.3 Performance
- Cache Redis para consultas frequentes
- Índices em campos de busca
- Paginação em todas as listagens
- Celery para operações pesadas