# Guia de Contribuição - LATECME

Obrigado por contribuir com o projeto LATECME! Este documento fornece diretrizes para garantir código de qualidade (code quality) e consistência no projeto.

## Índice

- [Configuração do Ambiente](#configuração-do-ambiente)
- [Padrões de Código](#padrões-de-código)
- [Workflow de Desenvolvimento](#workflow-de-desenvolvimento)
- [Ferramentas de Qualidade de Código](#ferramentas-de-qualidade-de-código)
- [Como Lidar com Erros Comuns](#como-lidar-com-erros-comuns)
- [Convenções de Importação](#convenções-de-importação)
- [Commits e Pull Requests](#commits-e-pull-requests)

## Configuração do Ambiente

### Requisitos

- Python 3.10+
- Poetry (gerenciador de dependências)
- Docker e Docker Compose (para desenvolvimento)

### Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd LATECME

# Instale as dependências de desenvolvimento
poetry install --with dev

# Configure o ambiente
cp .env.example .env
# Edite o .env com suas configurações locais

# Inicie os serviços de desenvolvimento
make dev-up
```

## Padrões de Código

### Estilo de Código

Este projeto segue as convenções PEP 8 com as seguintes especificações:

- **Comprimento de linha**: 88 caracteres (padrão Black)
- **Aspas**: Aspas duplas para strings
- **Indentação**: 4 espaços
- **Versão Python alvo**: 3.10+

### Organização de Imports

Os imports devem seguir a ordem (configurada via ruff/isort):

1. **Future imports** (ex: `from __future__ import annotations`)
2. **Standard library** (ex: `import os`, `from typing import List`)
3. **Third-party** (ex: `import django`, `from rest_framework import ...`)
4. **First-party** (módulos `apps` e `config`)
5. **Local folder** (imports relativos)

Exemplo correto:

```python
from __future__ import annotations

import os
from typing import Any, Dict

from django.db import models
from django.contrib.auth import get_user_model

from apps.materials.models import Material
from config.settings import BASE_DIR

from .utils import calculate_total
```

### Convenções de Nomenclatura

- **Módulos e pacotes**: `snake_case`
- **Classes**: `PascalCase`
- **Funções e variáveis**: `snake_case`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Métodos privados**: `_prefixo_com_underscore`

## Workflow de Desenvolvimento

### Antes de Começar a Codificar

1. **Crie uma branch** para sua funcionalidade ou correção:
   ```bash
   git checkout -b feature/nome-da-funcionalidade
   ```

2. **Certifique-se** de que o ambiente está atualizado:
   ```bash
   poetry install --with dev
   ```

### Durante o Desenvolvimento

Execute as verificações de código frequentemente:

```bash
# Verificar linting
make lint

# Formatar código automaticamente
make format

# Verificar tipos
make typecheck

# Verificar segurança
make security

# Executar todas as verificações
make quality
```

### Workflow de Pre-Commit (Recomendado)

Antes de fazer cada commit, execute:

```bash
# 1. Formate o código
make format

# 2. Execute todas as verificações
make quality

# 3. Se tudo estiver OK, faça o commit
git add .
git commit -m "Descrição clara da mudança"
```

**Dica**: Configure seu editor para formatar automaticamente ao salvar (veja seção de Integração com Editor).

## Ferramentas de Qualidade de Código

### Ruff - Linter e Formatter

Ruff é uma ferramenta extremamente rápida que substitui flake8, isort, black e outras.

#### Comandos Principais

```bash
# Verificar problemas
poetry run ruff check apps/ config/

# Corrigir problemas automaticamente
poetry run ruff check apps/ config/ --fix

# Formatar código
poetry run ruff format apps/ config/

# Verificar se código está formatado (sem modificar)
poetry run ruff format apps/ config/ --check
```

#### Regras Ativadas

- **E, F**: pycodestyle e Pyflakes (erros básicos)
- **I**: isort (ordenação de imports)
- **N**: pep8-naming (convenções de nomenclatura)
- **B**: bugbear (bugs comuns)
- **DJ**: Django-specific (boas práticas Django)
- **SIM**: simplify (simplificações de código)
- **UP**: pyupgrade (modernização Python)

Configuração completa em `pyproject.toml` seção `[tool.ruff]`.

### Mypy - Verificador de Tipos

Mypy verifica tipos estáticos para prevenir erros.

#### Comandos Principais

```bash
# Verificar tipos em todo o projeto
poetry run mypy apps/

# Verificar um módulo específico
poetry run mypy apps/materials/
```

#### Como Lidar com Erros de Tipo

**Erro**: `error: Function is missing a return type annotation`

```python
# ❌ Errado
def get_material(id):
    return Material.objects.get(pk=id)

# ✅ Correto
def get_material(id: int) -> Material:
    return Material.objects.get(pk=id)
```

**Erro**: `error: Argument 1 has incompatible type "str"; expected "int"`

```python
# ❌ Errado
material_id = "123"
get_material(material_id)

# ✅ Correto
material_id = 123
get_material(material_id)
```

**Quando usar `# type: ignore`**: Apenas em casos específicos onde o tipo é dinâmico ou complexo demais:

```python
# Use com moderação e sempre com comentário explicativo
result = some_complex_third_party_function()  # type: ignore  # API retorna Any
```

### Bandit - Scanner de Segurança

Bandit identifica problemas de segurança no código.

#### Comandos Principais

```bash
# Escanear todo o projeto
poetry run bandit -r apps/ config/ -c pyproject.toml

# Escanear com saída detalhada
poetry run bandit -r apps/ config/ -c pyproject.toml -v
```

#### Problemas Comuns e Soluções

**B201**: Uso de `pickle` - Evite usar pickle com dados não confiáveis.

**B301**: Uso de `eval()` - Nunca use `eval()` com input de usuário.

**B601**: SQL Injection - Use sempre Django ORM ou queries parametrizadas.

```python
# ❌ Errado - SQL Injection
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")

# ✅ Correto - Query parametrizada
cursor.execute("SELECT * FROM users WHERE name = %s", [user_input])

# ✅ Melhor - Django ORM
User.objects.filter(name=user_input)
```

## Como Lidar com Erros Comuns

### Erros de Linting (Ruff)

#### E501: Line too long

```python
# ❌ Evite linhas muito longas
very_long_function_name(argument1, argument2, argument3, argument4, argument5, argument6, argument7)

# ✅ Quebre em múltiplas linhas
very_long_function_name(
    argument1,
    argument2,
    argument3,
    argument4,
    argument5,
    argument6,
    argument7,
)
```

#### F401: Imported but unused

```python
# ❌ Import não utilizado
from django.db import models
from django.contrib.auth import get_user_model  # Não usado

# ✅ Remova imports não utilizados
from django.db import models
```

#### DJ001: Avoid null=True on string fields

```python
# ❌ Evite null=True em campos de texto
description = models.CharField(max_length=255, null=True, blank=True)

# ✅ Use string vazia como padrão
description = models.CharField(max_length=255, blank=True, default="")
```

### Erros de Formatação

Se o código não está formatado corretamente, simplesmente execute:

```bash
make format
```

O ruff formatará automaticamente todo o código de acordo com as regras configuradas.

## Convenções de Importação

### Ordem de Imports (isort)

```python
# 1. Future imports
from __future__ import annotations

# 2. Standard library
import os
import sys
from typing import Any, Dict, List

# 3. Third-party packages
import django
from django.db import models
from rest_framework.views import APIView

# 4. First-party (apps locais)
from apps.materials.models import Material
from apps.inventory.services import InventoryService
from config.settings import DEBUG

# 5. Local/relative imports
from .models import LocalModel
from .utils import helper_function
```

### Convenções Django-Specific

#### Models

```python
# Sempre importe models do Django
from django.db import models

# Para referências a modelos, use strings quando houver dependência circular
class Material(models.Model):
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.CASCADE)
```

#### Views

```python
# Prefira class-based views
from django.views.generic import ListView, DetailView

class MaterialListView(ListView):
    model = Material
    template_name = "materials/material_list.html"
```

## Commits e Pull Requests

### Mensagens de Commit

Siga o padrão de commits semânticos:

```
tipo(escopo): descrição curta

Descrição mais detalhada se necessário.

- Item relevante 1
- Item relevante 2
```

**Tipos**:
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação, sem mudança de lógica
- `refactor`: Refatoração de código
- `test`: Adição/modificação de testes
- `chore`: Tarefas de manutenção

**Exemplos**:
```bash
git commit -m "feat(materials): adicionar filtro por tipo de material"
git commit -m "fix(inventory): corrigir cálculo de peso total"
git commit -m "docs(readme): atualizar instruções de instalação"
```

### Pull Requests

Antes de abrir um Pull Request:

1. ✅ Certifique-se de que **todos os testes passam**
2. ✅ Execute `make quality` e corrija todos os problemas
3. ✅ Atualize a documentação se necessário
4. ✅ Adicione testes para novas funcionalidades
5. ✅ Rebase com a branch principal se necessário

**Template de PR**:

```markdown
## Descrição
[Descreva o que foi alterado e por quê]

## Tipo de mudança
- [ ] Bug fix
- [ ] Nova funcionalidade
- [ ] Breaking change
- [ ] Documentação

## Checklist
- [ ] Código segue os padrões do projeto
- [ ] `make quality` passa sem erros
- [ ] Testes adicionados/atualizados
- [ ] Documentação atualizada

## Como testar
[Instruções para testar as mudanças]
```

## Integração com Editor

### VS Code

Instale as extensões:
- **Ruff** (charliermarsh.ruff)
- **Mypy Type Checker** (ms-python.mypy-type-checker)

Adicione ao `settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },
  "ruff.lint.args": ["--config=pyproject.toml"],
  "mypy-type-checker.args": ["--config-file=pyproject.toml"]
}
```

### PyCharm

1. Vá em **Settings → Tools → External Tools**
2. Adicione ferramentas para ruff, mypy e bandit
3. Configure **File Watchers** para executar automaticamente

### Vim/Neovim

Use plugins como:
- **ALE** (Asynchronous Lint Engine)
- **coc.nvim** com coc-ruff e coc-mypy
- **null-ls.nvim** para integração com LSP

## Recursos Adicionais

- [Documentação Ruff](https://docs.astral.sh/ruff/)
- [Documentação Mypy](https://mypy.readthedocs.io/)
- [Documentação Bandit](https://bandit.readthedocs.io/)
- [PEP 8 - Style Guide](https://pep8.org/)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)

## Dúvidas?

Se tiver dúvidas ou precisar de ajuda:
1. Consulte a documentação das ferramentas
2. Verifique issues existentes no repositório
3. Abra uma issue para discussão

---

**Lembre-se**: Código de qualidade é código que seus colegas conseguem entender e manter facilmente. Obrigado por contribuir para manter este projeto com alta qualidade! 🚀
