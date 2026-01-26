# Correção: Loop de Redirecionamento (ERR_TOO_MANY_REDIRECTS)

## Problema Identificado

Ao acessar `http://127.0.0.1:8000/`, o navegador apresentava erro:
```
ERR_TOO_MANY_REDIRECTS
127.0.0.1 redirected you too many times.
```

## Causa Raiz

O problema era causado por um **loop de redirecionamento** entre três componentes:

1. **URL raiz (`/`)**: Redirecionava para `accounts:login`
2. **Middleware `UserApprovalMiddleware`**: Bloqueava usuários sem aprovação e redirecionava para login
3. **`CustomLoginView`**: Com `redirect_authenticated_user = True`, redirecionava usuários autenticados

### Cenário do Loop

```
Usuário autenticado mas sem aprovação acessa /
    ↓
Redirecionado para /accounts/login/
    ↓
CustomLoginView detecta usuário autenticado → redireciona para /dashboard/
    ↓
Middleware detecta usuário sem aprovação → redireciona para /accounts/login/
    ↓
CustomLoginView detecta usuário autenticado → redireciona para /dashboard/
    ↓
[LOOP INFINITO]
```

## Correções Aplicadas

### 1. Middleware (`apps/accounts/middleware.py`)

**Mudança 1**: Adicionada a raiz `/` às URLs isentas de verificação:

```python
EXEMPT_URLS = [
    '/',  # ← ADICIONADO
    '/accounts/login/',
    '/accounts/logout/',
    '/accounts/register/',
    '/accounts/register/success/',
    '/admin/',
    '/static/',
    '/media/',
]
```

**Mudança 2**: Prevenção de loop na própria página de login:

```python
# Verificar se o usuário pode acessar o sistema
if hasattr(request.user, 'can_access_system') and not request.user.can_access_system():
    # Evitar loop de redirecionamento: não redirecionar se já está na página de login
    if request.path == '/accounts/login/':
        return None

    # ... mensagens de erro ...
    return redirect('accounts:login')
```

### 2. LoginView (`apps/accounts/views.py`)

**Mudança**: Desabilitado redirecionamento automático e adicionado logout silencioso:

```python
class CustomLoginView(LoginView):
    redirect_authenticated_user = False  # ← MUDADO de True para False

    def dispatch(self, request, *args, **kwargs):
        # Se usuário está autenticado E pode acessar o sistema, redirecionar
        if request.user.is_authenticated:
            if hasattr(request.user, 'can_access_system') and request.user.can_access_system():
                return redirect(self.get_success_url())
            # Se está autenticado mas não pode acessar, fazer logout silencioso
            # para permitir novo login
            logout(request)

        return super().dispatch(request, *args, **kwargs)
```

### 3. Limpeza de Sessões

Criado script `clear_sessions.py` para limpar sessões antigas:

```bash
python clear_sessions.py
```

## Como Resolver Agora

### Opção 1: Limpar Sessões e Cookies

1. **Execute o script de limpeza**:
   ```bash
   venv/bin/python clear_sessions.py
   ```

2. **Limpe os cookies do navegador**:
   - Chrome/Edge: `Ctrl + Shift + Delete` → Cookies e dados de sites
   - Firefox: `Ctrl + Shift + Delete` → Cookies
   - Safari: Preferências → Privacidade → Gerenciar dados de sites

3. **Reinicie o servidor Django**:
   ```bash
   # Pare o servidor (Ctrl+C) e inicie novamente
   venv/bin/python manage.py runserver
   ```

4. **Acesse novamente**: http://127.0.0.1:8000/

### Opção 2: Usar Navegador Anônimo

Abra uma janela anônima/privativa (Ctrl+Shift+N no Chrome) e acesse:
```
http://127.0.0.1:8000/
```

Isso ignora cookies antigos.

## Validação das Correções

### Teste 1: Acesso Não Autenticado
```
GET http://127.0.0.1:8000/
  → Redireciona para /accounts/login/
  → Mostra formulário de login
  ✓ SEM LOOP
```

### Teste 2: Usuário Autenticado com Aprovação
```
POST /accounts/login/ (credenciais válidas, usuário aprovado)
  → Login bem-sucedido
  → Redireciona para /dashboard/
  ✓ ACESSO PERMITIDO
```

### Teste 3: Usuário Autenticado sem Aprovação
```
POST /accounts/login/ (credenciais válidas, usuário pendente)
  → Mensagem: "Sua conta ainda está aguardando aprovação."
  → Permanece em /accounts/login/
  → Logout silencioso
  ✓ SEM LOOP, MENSAGEM CLARA
```

### Teste 4: Usuário Sem Aprovação Tenta Acessar Dashboard
```
GET /dashboard/ (usuário autenticado mas pendente)
  → Middleware detecta falta de aprovação
  → Mensagem de aviso
  → Redireciona para /accounts/login/
  → Logout silencioso permite novo login
  ✓ SEM LOOP
```

## Prevenção de Problemas Futuros

### Boas Práticas Implementadas

1. **URLs Isentas**: Sempre incluir URLs públicas em `EXEMPT_URLS` do middleware
2. **Verificação de Loop**: Não redirecionar se já está na URL de destino
3. **Logout Silencioso**: Limpar sessões de usuários sem permissão
4. **Flags de Redirecionamento**: Desabilitar `redirect_authenticated_user` quando há lógica complexa

### Monitoramento

Se o problema voltar a ocorrer:

1. **Verifique logs do Django**:
   ```bash
   tail -f /var/log/django/debug.log  # se configurado
   ```

2. **Verifique requisições HTTP**:
   - Ferramentas de desenvolvedor do navegador (F12)
   - Aba "Network" para ver redirecionamentos
   - Procure por múltiplos 302 (redirect)

3. **Execute o script de limpeza**:
   ```bash
   venv/bin/python clear_sessions.py
   ```

## Arquivos Modificados

- ✅ `apps/accounts/middleware.py` (2 mudanças)
- ✅ `apps/accounts/views.py` (1 mudança)
- ✅ `clear_sessions.py` (novo arquivo)

## Commit das Correções

```bash
git add apps/accounts/middleware.py apps/accounts/views.py clear_sessions.py FIX_REDIRECT_LOOP.md
git commit -m "Corrigir loop de redirecionamento (ERR_TOO_MANY_REDIRECTS)

- Adicionar raiz (/) às EXEMPT_URLS do middleware
- Prevenir redirecionamento na própria página de login
- Desabilitar redirect_authenticated_user no LoginView
- Implementar logout silencioso para usuários sem aprovação
- Criar script clear_sessions.py para limpeza de sessões antigas"
```

## Resumo

✅ **Problema**: Loop de redirecionamento ao acessar raiz do site
✅ **Causa**: Conflito entre middleware, LoginView e sessões antigas
✅ **Solução**: 3 correções no código + limpeza de sessões
✅ **Status**: CORRIGIDO

---

**Data**: 2026-01-20
**Desenvolvido por**: Claude (Anthropic)
**Versão**: Django 5.2.4
