# Plano de Implementação: Web Designer de Etiquetas EPL

## Visão Geral

Criar um novo aplicativo Django `apps/labels/` que fornece:
- Designer visual drag-and-drop de etiquetas para contentores (Bins)
- Geração de comandos EPL (Eltron Programming Language)
- Comunicação TCP/IP com múltiplas impressoras de rede
- Sistema de templates reutilizáveis
- Histórico de trabalhos de impressão

## Requisitos Confirmados

**Tipo de Etiqueta**: Apenas Bins (contentores), com informações EXCLUSIVAS do contentor:
- Código do bin
- Localização (location_code)
- Armazém
- Capacidade
- Status
- Código de barras Code 128/39 com o código do bin

**Importante**: NÃO incluir informações do material que está dentro do bin (current_material, current_quantity, etc.)

**Interface**: Drag-and-drop WYSIWYG visual designer
**Impressoras**: Suporte a múltiplas impressoras com cadastro de IP:porta
**Códigos**: Códigos de barras 1D (Code 128, Code 39)

---

## Arquitetura da Solução

### Estrutura do App

```
apps/labels/
├── models.py              # LabelTemplate, PrinterConfiguration, PrintJob
├── views.py               # Views para designer, impressão, gerenciamento
├── urls.py                # Rotas do app
├── admin.py               # Admin para gerenciamento
├── epl_generator.py       # Geração de comandos EPL
├── printer_client.py      # Comunicação TCP/IP com impressoras
├── templates/labels/
│   ├── designer.html      # Interface drag-drop do designer
│   ├── template_list.html
│   ├── print_form.html    # Formulário de seleção impressora/template
│   └── print_preview.html
└── static/labels/
    ├── js/label_designer.js  # Lógica do canvas drag-drop
    └── css/designer.css
```

---

## Modelos de Dados

### 1. LabelTemplate
Armazena templates de etiquetas reutilizáveis.

**Campos principais**:
- `name`: Nome do template
- `description`: Descrição
- `width_mm`, `height_mm`: Dimensões em milímetros
- `printer_dpi`: Resolução (203 ou 300 DPI)
- `template_json`: JSONField com configuração dos elementos
- `is_default`: Template padrão

**Estrutura do template_json**:
```json
{
  "elements": [
    {
      "type": "text|barcode",
      "field": "code|location_code|warehouse|capacity|status",
      "x": 10,  // posição em mm
      "y": 10,
      "width": 50,
      "height": 10,
      "font_size": 2,
      "font_multiplier_h": 1,
      "font_multiplier_v": 1,
      "rotation": 0,
      "barcode_type": "128|39",
      "human_readable": true,
      "label": "Código:"  // texto estático opcional
    }
  ]
}
```

**Métodos auxiliares**:
- `width_dots`, `height_dots`: Conversão mm → dots baseado no DPI
- `mm_to_dots(mm)`: Converte milímetros para dots da impressora

### 2. PrinterConfiguration
Cadastro de impressoras de rede.

**Campos**:
- `name`: Nome da impressora
- `ip_address`: IP da impressora
- `port`: Porta TCP (padrão 9100)
- `timeout_seconds`: Timeout de conexão
- `default_warehouse`: Armazém padrão (opcional)
- `is_default`: Impressora padrão
- `last_test_date`, `last_test_success`: Status da última conexão

### 3. PrintJob
Histórico de trabalhos de impressão.

**Campos**:
- `printer`: FK para PrinterConfiguration
- `template`: FK para LabelTemplate
- `bin`: FK para Bin
- `status`: PENDING, PROCESSING, SUCCESS, FAILED, CANCELLED
- `epl_content`: Comandos EPL gerados
- `bin_data_snapshot`: JSON com dados do bin no momento da impressão
- `printed_at`: Timestamp de impressão
- `error_message`: Mensagem de erro se falhar

Todos os modelos herdam de `BaseModel` (UUID, audit trail, soft delete).

---

## Módulo de Geração EPL

**Arquivo**: `apps/labels/epl_generator.py`

**Classe**: `EPLGenerator`

### Responsabilidades:
1. Receber LabelTemplate e Bin como entrada
2. Gerar comandos EPL válidos baseado no template_json
3. Converter coordenadas de mm para dots
4. Gerar comandos de texto (comando `A`)
5. Gerar comandos de código de barras (comando `B`)

### Comandos EPL Principais:

**Inicialização**:
```
N                    # Nova etiqueta
Q<width>,0           # Largura da etiqueta
q<width>             # Largura do formulário
```

**Texto** (comando A):
```
Ah_pos,v_pos,rotation,font,h_mult,v_mult,reverse,"text"
```
- `h_pos`, `v_pos`: Posição em dots
- `rotation`: 0, 1, 2, 3 (0°, 90°, 180°, 270°)
- `font`: 1-5 (tamanhos de fonte)
- `h_mult`, `v_mult`: Multiplicadores 1-8
- `reverse`: N (normal) ou R (invertido)

**Código de Barras** (comando B):
```
Bh_pos,v_pos,rotation,type,narrow,wide,height,human,"data"
```
- `type`: 1 (Code 128), 3 (Code 39)
- `narrow`, `wide`: Largura das barras em dots
- `height`: Altura em dots
- `human`: B (mostrar texto) ou N (ocultar)

**Finalização**:
```
P1                   # Imprimir 1 cópia
```

### Mapeamento de Campos do Bin:
- `code` → `bin.code`
- `location_code` → `bin.location_code`
- `warehouse` → `bin.warehouse.code`
- `capacity` → `f"{bin.capacity} kg"`
- `status` → `bin.get_status_display()`

**Conversão mm → dots**: `dots = (mm / 25.4) * dpi`
- 203 DPI: 1mm ≈ 8 dots
- 300 DPI: 1mm ≈ 11.8 dots

---

## Módulo de Comunicação com Impressora

**Arquivo**: `apps/labels/printer_client.py`

**Classe**: `PrinterClient`

### Responsabilidades:
1. Estabelecer conexão TCP/IP com impressora
2. Enviar comandos EPL
3. Tratar timeouts e erros de rede
4. Testar conectividade

### Métodos:

**`send_epl(epl_content)`**:
- Cria socket TCP
- Conecta no IP:porta
- Envia EPL em bytes (codificação ASCII)
- Fecha conexão
- Retorna: `(success: bool, error_message: str)`

**`test_connection()`**:
- Testa conexão sem enviar dados
- Atualiza campos `last_test_date` e `last_test_success`
- Retorna: `(success: bool, message: str)`

### Tratamento de Erros:
- `socket.timeout`: Retornar erro de timeout
- `socket.error`: Retornar erro de conexão
- `Exception`: Retornar erro genérico
- Sempre fechar socket no `finally`

---

## Interface do Designer

**Arquivo**: `apps/labels/static/labels/js/label_designer.js`

**Classe JavaScript**: `LabelDesigner`

### Funcionalidades:

1. **Canvas de Design**:
   - Canvas HTML5 escalado para exibição (3 pixels por mm)
   - Grid de referência (linhas a cada 10mm)
   - Fundo branco com borda preta

2. **Elementos**:
   - Adicionar elementos texto/barcode via botões
   - Arrastar elementos no canvas
   - Selecionar elementos (highlight azul)
   - Deletar elementos selecionados

3. **Painel de Propriedades**:
   - Atualiza com dados do elemento selecionado
   - Inputs para: campo, posição (x, y), tamanho, fonte
   - Propriedades específicas por tipo (label para texto, barcode_type para código de barras)

4. **Salvamento**:
   - Serializar elementos para JSON
   - Enviar via AJAX POST para `/labels/templates/save/`
   - Salvar metadados (nome, dimensões, DPI)

### Eventos:
- `mousedown`: Detectar clique em elemento, iniciar drag
- `mousemove`: Atualizar posição durante drag
- `mouseup`: Finalizar drag
- Property inputs: Atualizar elemento em tempo real

### Renderização:
- Redesenhar canvas a cada mudança
- Mostrar representação visual de texto e códigos de barras
- Indicar elemento selecionado com borda azul

---

## Views Principais

### 1. `template_designer(request, template_id=None)`
Interface drag-and-drop para criar/editar templates.
- GET: Renderiza designer.html
- Se template_id: Carrega template existente

### 2. `template_save(request)`
Salva/atualiza template (AJAX POST).
- Recebe JSON com dados do template
- Cria ou atualiza LabelTemplate
- Retorna `{success: bool, template_id: uuid}`

### 3. `print_form(request, bin_id)`
Formulário para imprimir etiqueta de um bin.
- Listar templates disponíveis
- Listar impressoras disponíveis
- Pre-selecionar padrões (is_default=True)

### 4. `print_preview(request, bin_id, template_id)`
Preview da etiqueta antes de imprimir.
- Gerar EPL usando EPLGenerator
- Mostrar comandos EPL
- Botão para confirmar impressão

### 5. `print_label(request)`
Executa impressão (AJAX POST).
- Recebe: bin_id, template_id, printer_id
- Gera EPL com EPLGenerator
- Cria PrintJob com status PROCESSING
- Envia para impressora com PrinterClient
- Atualiza PrintJob com SUCCESS/FAILED
- Retorna resultado JSON

### 6. `printer_test(request, printer_id)`
Testa conexão com impressora (AJAX POST).
- Usa PrinterClient.test_connection()
- Retorna `{success: bool, message: str}`

---

## Integração com Views Existentes

### Arquivo a Modificar: `templates/inventory/bin_detail.html`

**Adicionar botão na seção "Ações Rápidas" (após linha 294)**:

```html
<div class="col-md-6 mb-2">
    <a href="{% url 'labels:print_form' bin.id %}" class="btn btn-primary btn-block">
        <i class="fa fa-print"></i><br>
        Imprimir Etiqueta
    </a>
</div>
```

**Localização**: Dentro da div "Quick Actions" do sidebar, junto com os outros botões de ação.

---

## URLs do App

**Arquivo**: `apps/labels/urls.py`

```python
app_name = 'labels'

urlpatterns = [
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/designer/', views.template_designer, name='template_designer'),
    path('templates/designer/<uuid:template_id>/', views.template_designer, name='template_designer_edit'),
    path('templates/save/', views.template_save, name='template_save'),

    # Impressão
    path('print/form/<uuid:bin_id>/', views.print_form, name='print_form'),
    path('print/preview/<uuid:bin_id>/<uuid:template_id>/', views.print_preview, name='print_preview'),
    path('print/execute/', views.print_label, name='print_label'),

    # Impressoras
    path('printers/', views.printer_list, name='printer_list'),
    path('printers/<uuid:printer_id>/test/', views.printer_test, name='printer_test'),
]
```

---

## Configuração do Projeto

### 1. Adicionar app em `config/settings.py`:

```python
INSTALLED_APPS = [
    # ... apps existentes
    "apps.labels",  # ADICIONAR
]
```

### 2. Adicionar URLs em `config/urls.py`:

```python
urlpatterns = [
    # ... URLs existentes
    path('labels/', include('apps.labels.urls')),  # ADICIONAR
]
```

### 3. Dependências (já disponíveis):
- Django 5.2.4 ✓
- Pillow (para processamento de imagens) ✓
- Python socket (built-in) ✓

**Nenhuma biblioteca adicional necessária!**

---

## Admin Configuration

**Arquivo**: `apps/labels/admin.py`

Registrar os 3 modelos com customizações:

1. **LabelTemplateAdmin**:
   - `list_display`: name, dimensions, printer_dpi, is_default
   - `list_filter`: is_default, printer_dpi
   - Fieldsets organizados

2. **PrinterConfigurationAdmin**:
   - `list_display`: name, connection_info (IP:porta), status_indicator (✓/✗)
   - `list_filter`: is_default, last_test_success
   - Botão para testar conexão

3. **PrintJobAdmin**:
   - `list_display`: created_at, bin_code, printer, status
   - `list_filter`: status, printer, created_at
   - Read-only: printed_at, error_message

---

## Ordem de Implementação

### Fase 1: Fundação (Dia 1-2)
1. ✅ Criar estrutura do app: `python manage.py startapp labels` em `apps/`
2. ✅ Definir modelos (LabelTemplate, PrinterConfiguration, PrintJob)
3. ✅ Criar migrações: `python manage.py makemigrations labels`
4. ✅ Aplicar migrações: `python manage.py migrate`
5. ✅ Configurar admin.py
6. ✅ Adicionar app em INSTALLED_APPS
7. ✅ Configurar URLs

### Fase 2: Lógica Central (Dia 3-4)
8. ✅ Implementar `epl_generator.py` (classe EPLGenerator)
9. ✅ Implementar `printer_client.py` (classe PrinterClient)
10. ✅ Criar views básicas (template CRUD, printer CRUD)
11. ✅ Testar geração EPL com dados de exemplo

### Fase 3: Interface do Designer (Dia 5-7)
12. ✅ Criar template HTML `designer.html`
13. ✅ Implementar `label_designer.js` (canvas, rendering)
14. ✅ Implementar drag-and-drop de elementos
15. ✅ Criar painel de propriedades
16. ✅ Implementar save/load de templates

### Fase 4: Sistema de Impressão (Dia 8-9)
17. ✅ Implementar view `print_form`
18. ✅ Implementar view `print_preview`
19. ✅ Implementar view `print_label` com PrintJob tracking
20. ✅ Testar comunicação TCP/IP real com impressora
21. ✅ Tratamento de erros e retry

### Fase 5: Integração (Dia 10)
22. ✅ Adicionar botão "Imprimir Etiqueta" em `bin_detail.html`
23. ✅ Criar templates HTML para todas as views
24. ✅ Aplicar estilos Bootstrap (Color Admin theme)
25. ✅ Tradução de strings para português

### Fase 6: Finalização (Dia 11-12)
26. ✅ Testes de fluxo completo
27. ✅ Testar cenários de erro (impressora offline, rede instável)
28. ✅ Criar dados iniciais (template padrão, exemplo de impressora)
29. ✅ Documentação de uso
30. ✅ Deploy e treinamento

---

## Arquivos Críticos para Implementação

### 1. `/home/felipe/work/LATECME/apps/labels/models.py`
Define a estrutura de dados completa: LabelTemplate com conversão mm→dots, PrinterConfiguration com validação de IP/porta, PrintJob com tracking de status.

### 2. `/home/felipe/work/LATECME/apps/labels/epl_generator.py`
Motor de geração EPL: converte template JSON + dados do Bin em comandos EPL válidos (comandos A para texto, B para códigos de barras).

### 3. `/home/felipe/work/LATECME/apps/labels/static/labels/js/label_designer.js`
Interface drag-and-drop: canvas HTML5 com elementos arrastáveis, painel de propriedades dinâmico, serialização para JSON.

### 4. `/home/felipe/work/LATECME/apps/labels/views.py`
Orquestração: designer de templates, preview de etiquetas, execução de impressão com tratamento de erros, gerenciamento de impressoras.

### 5. `/home/felipe/work/LATECME/apps/labels/printer_client.py`
Comunicação TCP/IP: conexão socket, envio de EPL em bytes, tratamento de timeout/erros, teste de conectividade.

### 6. `/home/felipe/work/LATECME/templates/inventory/bin_detail.html`
Ponto de integração: adicionar botão "Imprimir Etiqueta" na seção Quick Actions (linha ~294).

---

## Verificação e Testes

### Testes Unitários:
1. **EPLGenerator**:
   - Testar conversão mm→dots
   - Validar comandos EPL gerados
   - Verificar mapeamento correto de campos do Bin

2. **PrinterClient**:
   - Testar conexão bem-sucedida
   - Testar timeout
   - Testar erro de rede

3. **Models**:
   - Validar template_json structure
   - Testar is_default (apenas um por vez)
   - Testar conversões width_dots/height_dots

### Testes de Integração:
1. Criar template no designer → Salvar → Recarregar
2. Selecionar bin → Escolher template → Preview EPL
3. Imprimir etiqueta → Verificar PrintJob criado
4. Testar impressora offline → Verificar erro tratado

### Testes End-to-End:
1. Criar template com texto + barcode
2. Imprimir etiqueta de bin real
3. Verificar etiqueta física impressa corretamente
4. Validar código de barras escaneável

### Comandos de Teste:

```bash
# Criar migrações
python manage.py makemigrations labels

# Aplicar migrações
python manage.py migrate

# Criar superuser (se necessário)
python manage.py createsuperuser

# Rodar servidor
python manage.py runserver

# Acessar:
# - Designer: http://localhost:8000/labels/templates/designer/
# - Admin: http://localhost:8000/admin/
# - Bin detail: http://localhost:8000/inventory/bins/<uuid>/
```

---

## Considerações Técnicas

### Sistema de Coordenadas:
- **Canvas (tela)**: Pixels escalados (3px por mm para visualização)
- **Template JSON**: Milímetros (unidade física)
- **EPL**: Dots (depende do DPI da impressora)
- **Conversão**: Screen px → MM → Dots

### Validações:
- Elementos não podem exceder dimensões da etiqueta
- Dados de código de barras devem ser válidos (alfanuméricos para Code 39)
- Verificar dimensões mínimas de códigos de barras
- Validar IP/porta da impressora

### Performance:
- Criar índices em PrintJob.created_at e PrintJob.status
- Usar select_related para queries de PrintJob (printer, template, bin)
- Canvas: debounce no drag para evitar re-renders excessivos

### Segurança:
- Validar input de IP (GenericIPAddressField)
- Validar JSON do template antes de salvar
- Sanitizar dados do bin antes de incluir em EPL
- Proteção CSRF em todos os POSTs

---

## Dados Iniciais Sugeridos

### Template Padrão (via Django Admin ou fixture):
```python
LabelTemplate.objects.create(
    name="Etiqueta Padrão Contentor",
    description="Template padrão para etiquetas de contentores",
    width_mm=100,
    height_mm=50,
    printer_dpi=203,
    is_default=True,
    template_json={
        "elements": [
            {
                "type": "text",
                "field": "code",
                "x": 5,
                "y": 5,
                "width": 40,
                "height": 8,
                "font_size": 4,
                "font_multiplier_h": 2,
                "font_multiplier_v": 2,
                "rotation": 0,
                "label": ""
            },
            {
                "type": "barcode",
                "field": "code",
                "x": 5,
                "y": 20,
                "width": 80,
                "height": 15,
                "barcode_type": "128",
                "human_readable": True,
                "rotation": 0
            },
            {
                "type": "text",
                "field": "warehouse",
                "x": 5,
                "y": 40,
                "width": 30,
                "height": 6,
                "font_size": 2,
                "label": "Armazém:"
            },
            {
                "type": "text",
                "field": "location_code",
                "x": 50,
                "y": 40,
                "width": 40,
                "height": 6,
                "font_size": 2,
                "label": "Local:"
            }
        ]
    },
    created_by=<admin_user>,
    updated_by=<admin_user>
)
```

---

## Referências Técnicas

**EPL (Eltron Programming Language)**:
- Comandos de texto: `A` (ASCII text)
- Comandos de barcode: `B` (1D barcodes)
- Comandos de controle: `N` (new label), `P` (print), `Q` (label width)
- Rotação: 0=0°, 1=90°, 2=180°, 3=270°
- Fontes: 1 (8x12), 2 (10x16), 3 (12x20), 4 (14x24), 5 (32x48)

**Resolução**:
- 203 DPI: Padrão para etiquetas de estoque
- 300 DPI: Alta resolução para detalhes pequenos
- Conversão: `dots = (mm ÷ 25.4) × DPI`

**Porta TCP padrão**: 9100 (raw print protocol)

---

## Resumo

Este plano implementa um sistema completo de design e impressão de etiquetas EPL integrado ao LATECME:

✅ Designer visual drag-and-drop intuitivo
✅ Templates reutilizáveis salvos em JSON
✅ Geração automática de comandos EPL
✅ Suporte a múltiplas impressoras de rede
✅ Códigos de barras Code 128 e Code 39
✅ Histórico completo de trabalhos de impressão
✅ Integração nativa com modelo Bin
✅ Interface em português (pt-br)
✅ Sem dependências externas adicionais

O sistema segue todos os padrões do projeto LATECME: herança de BaseModel, audit trail completo, soft delete, UUID como chave primária, e integração com o tema Color Admin Bootstrap.
