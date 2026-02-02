# Relatório de Inconsistências Visuais - LATECME

**Data:** 02/02/2026
**Analisado por:** Jarvis (AI Assistant)

---

## Resumo Executivo

Após análise detalhada dos 50 templates HTML do sistema LATECME, foram identificadas diversas inconsistências visuais e de padrão que afetam a homogeneidade da interface. Este relatório documenta os problemas encontrados e propõe soluções para padronização.

---

## 1. Inconsistências na Estrutura de Filtros

### Problema
Os filtros de busca apresentam três padrões diferentes nas telas de listagem:

| Template | Padrão Usado |
|----------|--------------|
| material_list.html | Filtros inline dentro do card principal |
| stock_list.html | Card separado com título "Filtros" e ícone |
| production_order_list.html | Card separado sem título |
| purchasing/order_list.html | Card separado sem título |

### Recomendação
Padronizar para **Card separado com título "Filtros"** usando ícone `tabler-filter`:

```html
<div class="card mb-3">
    <div class="card-header">
        <h3 class="card-title">
            <svg class="icon icon-tabler me-2">...</svg>
            Filtros
        </h3>
    </div>
    <div class="card-body">
        <!-- formulário de filtros -->
    </div>
</div>
```

**Arquivos a corrigir:**
- `templates/materials/material_list.html`
- `templates/materials/supplier_list.html`
- `templates/production/production_order_list.html`
- `templates/purchasing/order_list.html`

---

## 2. Inconsistências na Paginação

### Problema
Três padrões diferentes de paginação:

1. **Completo** (material_list.html): Números de página + ícones de seta
2. **Texto** (stock_list.html): "Anterior" e "Próximo" como texto
3. **Misto** (production_order_list.html): Ícones + texto

### Recomendação
Padronizar para paginação completa com:
- Ícones de seta (`tabler-chevron-left/right`)
- Números de página (range -3 a +3)
- Texto complementar após ícone ("Anterior", "Próximo")

**Arquivos a corrigir:**
- `templates/inventory/stock_list.html`
- `templates/inventory/movements_list.html`
- `templates/inventory/warehouse_list.html`
- `templates/purchasing/order_list.html`
- `templates/purchasing/request_list.html`
- `templates/purchasing/receiving_list.html`

---

## 3. Inconsistências nos Cards de Estatísticas

### Problema
- Algumas telas têm cards de estatísticas no topo (production, purchasing)
- Outras não têm (materials, inventory)

### Recomendação
Adicionar cards de estatísticas em todas as telas de listagem principal usando a estrutura:

```html
<div class="row row-deck row-cards mb-3">
    <div class="col-sm-6 col-lg-3">
        <div class="card card-sm">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-auto">
                        <span class="bg-{cor} text-white avatar">
                            <svg>...</svg>
                        </span>
                    </div>
                    <div class="col">
                        <div class="font-weight-medium">{{ valor }}</div>
                        <div class="text-muted">{{ label }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- ... mais cards ... -->
</div>
```

**Arquivos a corrigir:**
- `templates/materials/material_list.html` - Adicionar estatísticas
- `templates/inventory/stock_list.html` - Adicionar estatísticas

---

## 4. Inconsistências nos Botões de Ação

### Problema
Variação nos estilos de botões de ação nas tabelas:

| Estilo | Uso |
|--------|-----|
| `btn btn-icon btn-sm btn-primary` | material_list.html |
| `btn btn-icon btn-ghost-primary` | production_order_list.html |
| `btn btn-primary btn-sm` | stock_list.html |

### Recomendação
Padronizar para `btn btn-icon btn-ghost-{variante}` para ações em tabelas:

```html
<a href="..." class="btn btn-icon btn-ghost-primary" title="Ver detalhes">
    <svg>...</svg>
</a>
<a href="..." class="btn btn-icon btn-ghost-warning" title="Editar">
    <svg>...</svg>
</a>
```

**Arquivos a corrigir:**
- `templates/materials/material_list.html`
- `templates/materials/supplier_list.html`
- `templates/inventory/stock_list.html`
- `templates/inventory/movements_list.html`

---

## 5. Inconsistências na Acentuação

### Problema Crítico
Muitos textos estão **sem acentuação** (ASCII puro), prejudicando a experiência do usuário brasileiro:

| Texto Atual | Correção |
|-------------|----------|
| Producao | Produção |
| Movimentacoes | Movimentações |
| Armazens | Armazéns |
| Solicitacoes | Solicitações |
| Relatorios | Relatórios |
| Documentacao | Documentação |
| Acoes | Ações |
| Codigo | Código |
| Proximo | Próximo |
| Numero | Número |

### Recomendação
Fazer busca e substituição em todos os templates para corrigir acentuação.

**Comando sugerido:**
```bash
find templates/ -name "*.html" -exec sed -i \
    -e 's/Producao/Produção/g' \
    -e 's/Movimentacoes/Movimentações/g' \
    -e 's/Armazens/Armazéns/g' \
    -e 's/Solicitacoes/Solicitações/g' \
    -e 's/Relatorios/Relatórios/g' \
    -e 's/Documentacao/Documentação/g' \
    -e 's/Acoes/Ações/g' \
    -e 's/Codigo/Código/g' \
    -e 's/Proximo/Próximo/g' \
    -e 's/Numero/Número/g' \
    {} \;
```

---

## 6. Inconsistências nos Empty States

### Problema
Variação na estrutura de estados vazios:

- Alguns têm botão de ação
- Alguns têm mensagem contextual (filtros vs. dados)
- Ícones inconsistentes

### Recomendação
Criar componente reutilizável `templates/components/_empty_state.html`:

```html
{% comment %}
Uso: {% include 'components/_empty_state.html' with icon='packages' title='Nenhum item' subtitle='Cadastre o primeiro' action_url='/novo/' action_text='Novo Item' %}
{% endcomment %}

<div class="empty">
    <div class="empty-icon">
        <svg class="icon icon-lg">
            <use href="{% static 'icons/tabler-sprite.svg' %}#tabler-{{ icon }}"></use>
        </svg>
    </div>
    <p class="empty-title">{{ title }}</p>
    {% if subtitle %}
    <p class="empty-subtitle text-muted">{{ subtitle }}</p>
    {% endif %}
    {% if action_url %}
    <div class="empty-action">
        <a href="{{ action_url }}" class="btn btn-primary">
            <svg class="icon"><use href="...#tabler-plus"></use></svg>
            {{ action_text }}
        </a>
    </div>
    {% endif %}
</div>
```

---

## 7. Inconsistências em Labels de Formulário

### Problema
- Uso inconsistente da classe `required` em labels obrigatórios
- Alguns formulários usam `<label class="form-label required">`, outros não

### Recomendação
Adicionar classe `required` em todos os labels de campos obrigatórios:

```html
<label class="form-label required">Campo Obrigatório</label>
```

---

## 8. Inconsistências no Header do Card de Tabela

### Problema
Variação na estrutura do header dos cards de listagem:

| Template | Estrutura |
|----------|-----------|
| material_list.html | Título + badge de contagem |
| stock_list.html | Título + badge de contagem |
| production_order_list.html | Ícone + Título + badge + checkbox "Selecionar todos" |

### Recomendação
Padronizar para:

```html
<div class="card-header">
    <h3 class="card-title">
        <svg class="icon me-2">...</svg>
        {{ título }}
        <span class="badge bg-secondary ms-2">{{ total }}</span>
    </h3>
    {% if has_bulk_actions %}
    <div class="card-actions">
        <!-- ações em lote -->
    </div>
    {% endif %}
</div>
```

---

## 9. Inconsistências no Modal de Criação

### Problema
Diferentes formas de implementar modais Alpine.js:

1. Usando `x-show` + `:class`
2. Usando apenas `:class`
3. Diferentes estruturas de backdrop

### Recomendação
Padronizar estrutura de modal:

```html
<div class="modal modal-blur fade"
     x-show="modalOpen"
     :class="{ 'show d-block': modalOpen }"
     x-cloak
     @keydown.escape.window="modalOpen = false">
    <div class="modal-dialog" @click.outside="modalOpen = false">
        <!-- conteúdo -->
    </div>
</div>
<div class="modal-backdrop fade"
     x-show="modalOpen"
     :class="{ 'show': modalOpen }"
     x-cloak></div>
```

---

## 10. CSS Custom - Melhorias Sugeridas

### Adicionar ao `static/css/custom.css`:

```css
/* Padronização de badges de status */
.badge-status-draft { background-color: var(--tblr-secondary); }
.badge-status-pending { background-color: var(--tblr-yellow); }
.badge-status-active { background-color: var(--tblr-cyan); }
.badge-status-completed { background-color: var(--tblr-green); }
.badge-status-cancelled { background-color: var(--tblr-dark); }

/* Card de filtros consistente */
.card-filters .card-header {
    background: rgba(var(--tblr-primary-rgb), 0.05);
}

/* Transição suave para hover em linhas de tabela */
.table-hover tbody tr {
    transition: background-color 0.15s ease-in-out;
}

/* Espaçamento consistente para botões de ação em tabela */
.table .btn-list {
    gap: 0.25rem;
}
```

---

## Plano de Ação Priorizado

### Alta Prioridade (Impacto Visual Imediato)
1. ✅ Corrigir acentuação em todos os templates
2. ✅ Padronizar estrutura de filtros
3. ✅ Padronizar paginação

### Média Prioridade (Consistência)
4. ⏳ Padronizar botões de ação em tabelas
5. ⏳ Adicionar cards de estatísticas onde faltam
6. ⏳ Criar componente de empty state reutilizável

### Baixa Prioridade (Refinamento)
7. ⏳ Padronizar estrutura de modais
8. ⏳ Adicionar CSS custom para badges de status
9. ⏳ Revisar labels de formulários

---

## Arquivos Mais Críticos para Correção

1. `templates/materials/material_list.html`
2. `templates/inventory/stock_list.html`
3. `templates/purchasing/order_list.html`
4. `templates/production/production_order_list.html`
5. `templates/base/internal.html` (sidebar com acentos)

---

## Conclusão

O sistema LATECME possui uma base sólida usando Tabler CSS, HTMX e Alpine.js. As inconsistências identificadas são principalmente de **padronização** e não afetam a funcionalidade. Com as correções propostas, a interface ficará mais homogênea e profissional.

**Esforço estimado:** 8-12 horas de desenvolvimento para aplicar todas as correções.
