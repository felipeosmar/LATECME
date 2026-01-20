# Sistema de Etiquetas EPL

Sistema completo de design e impressão de etiquetas para contentores (Bins) usando EPL (Eltron Programming Language).

## Funcionalidades

### ✅ Designer Visual
- Interface drag-and-drop para criação de templates
- Canvas HTML5 com visualização em tempo real
- Elementos de texto e código de barras (Code 128, Code 39)
- Painel de propriedades dinâmico
- Salvamento de templates reutilizáveis

### ✅ Impressão de Etiquetas
- Seleção de template e impressora
- Preview de comandos EPL antes de imprimir
- Comunicação TCP/IP direta com impressoras
- Histórico completo de trabalhos de impressão

### ✅ Gerenciamento de Impressoras
- Cadastro de múltiplas impressoras de rede
- Teste de conectividade TCP/IP
- Configuração de IP, porta e timeout
- Status de última verificação

## Configuração Inicial

### 1. Criar Dados Iniciais

Execute o script de criação de dados iniciais:

```bash
python create_labels_initial_data.py
```

Isto criará:
- Template padrão de etiqueta para bins (100x50mm, 203 DPI)
- Impressora de exemplo (configure o IP correto no admin)

### 2. Configurar Impressoras

Acesse o Django Admin:

```
http://localhost:8000/admin/labels/printerconfiguration/
```

Configure:
- **IP Address**: IP da impressora na rede local
- **Port**: Porta TCP (padrão: 9100)
- **Timeout**: Tempo de espera em segundos (padrão: 5)
- **Default Warehouse**: Armazém padrão (opcional)
- **Is Default**: Marcar como impressora padrão

Teste a conexão clicando no botão de teste no admin ou em `/labels/printers/`.

### 3. Configurar Templates

Opções:

1. **Usar template padrão**: Já está criado e funcional
2. **Criar novo template**: Acesse `/labels/templates/designer/`

## Uso

### Imprimir Etiqueta de um Bin

1. Acesse a página de detalhes de um contentor
2. Clique no botão **"Imprimir Etiqueta"** (Quick Actions sidebar)
3. Selecione o template e impressora
4. Clique em **"Visualizar Preview"** (opcional) ou **"Imprimir Agora"**

### Criar/Editar Templates

1. Acesse `/labels/templates/`
2. Clique em **"Novo Template"**
3. Configure dimensões e resolução
4. Use a toolbox para adicionar:
   - **Texto**: Campos do bin com labels opcionais
   - **Código de Barras**: Code 128 ou Code 39
5. Arraste elementos para posicionar
6. Configure propriedades no painel lateral
7. Salve o template

#### Campos Disponíveis

- `code`: Código do contentor
- `location_code`: Código de localização
- `warehouse`: Código do armazém
- `capacity`: Capacidade em kg
- `status`: Status do contentor

## Estrutura do Template JSON

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
      "font_size": 2,  // 1-5 (apenas texto)
      "font_multiplier_h": 1,  // 1-8 (apenas texto)
      "font_multiplier_v": 1,  // 1-8 (apenas texto)
      "rotation": 0,  // 0, 1, 2, 3 (0°, 90°, 180°, 270°)
      "barcode_type": "128|39",  // apenas barcode
      "human_readable": true,  // apenas barcode
      "label": "Código:"  // texto estático opcional (apenas texto)
    }
  ]
}
```

## Comandos EPL

### Estrutura Básica

```
N                    # Nova etiqueta
Q<width>,0           # Largura da etiqueta
q<width>             # Largura do formulário
A<params>,"text"     # Texto
B<params>,"data"     # Código de barras
P1                   # Imprimir 1 cópia
```

### Comando de Texto (A)

```
Ah_pos,v_pos,rotation,font,h_mult,v_mult,reverse,"text"
```

- `h_pos`, `v_pos`: Posição em dots
- `rotation`: 0-3 (0°, 90°, 180°, 270°)
- `font`: 1-5 (tamanhos)
- `h_mult`, `v_mult`: Multiplicadores 1-8
- `reverse`: N (normal) ou R (invertido)

### Comando de Código de Barras (B)

```
Bh_pos,v_pos,rotation,type,narrow,wide,height,human,"data"
```

- `type`: 1 (Code 128), 3 (Code 39)
- `narrow`, `wide`: Largura das barras
- `height`: Altura em dots
- `human`: B (mostrar texto) ou N (ocultar)

## Conversão de Unidades

### Milímetros para Dots

```
dots = (mm / 25.4) × DPI
```

Exemplos:
- **203 DPI**: 1mm ≈ 8 dots
- **300 DPI**: 1mm ≈ 11.8 dots

## Troubleshooting

### Impressora Não Conecta

1. Verifique se o IP está correto
2. Teste conectividade: `ping <IP_DA_IMPRESSORA>`
3. Verifique se a porta 9100 está aberta
4. Confira firewall/rede

### Etiqueta Não Imprime Corretamente

1. Verifique DPI do template (deve corresponder à impressora)
2. Confira dimensões da etiqueta física
3. Verifique preview dos comandos EPL
4. Teste com template padrão

### Elementos Não Aparecem

1. Verifique se estão dentro das dimensões da etiqueta
2. Confirme coordenadas (x, y) positivas
3. Verifique tamanho (width, height) adequados

## URLs Disponíveis

| URL | Descrição |
|-----|-----------|
| `/labels/templates/` | Lista de templates |
| `/labels/templates/designer/` | Criar novo template |
| `/labels/templates/designer/<id>/` | Editar template |
| `/labels/printers/` | Lista de impressoras |
| `/labels/jobs/` | Histórico de impressões |
| `/labels/print/form/<bin_id>/` | Formulário de impressão |
| `/labels/print/preview/<bin_id>/<template_id>/` | Preview EPL |

## Modelos

### LabelTemplate
- Armazena templates reutilizáveis
- JSON com elementos (texto, barcode)
- Conversão automática mm → dots

### PrinterConfiguration
- Configuração de impressoras TCP/IP
- Status de última verificação
- Impressora padrão

### PrintJob
- Histórico de trabalhos
- Snapshot de dados do bin
- Comandos EPL gerados
- Status (SUCCESS, FAILED, etc.)

## Segurança

- CSRF protection em todos os POSTs
- Validação de IP addresses
- Sanitização de dados do bin
- Soft delete em todos os modelos
- Audit trail completo (created_by, updated_by)

## Dependências

Nenhuma biblioteca adicional necessária! O sistema usa apenas:
- Django 5.2.4+
- Python socket (built-in)
- Canvas HTML5 (frontend)

## Contribuindo

Ao adicionar novos campos ao modelo Bin:

1. Atualize `epl_generator.py` → método `_get_bin_field_value()`
2. Atualize `label_designer.js` → método `getFieldDisplayName()`
3. Adicione opção no select de campos em `showElementProperties()`

## Licença

Este módulo faz parte do sistema LATECME.
