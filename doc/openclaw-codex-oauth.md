# OpenClaw — OAuth do Codex (OpenAI)

Como funciona a autenticação OAuth do Codex no OpenClaw: fluxo completo, onde os tokens ficam gravados e como editar manualmente.

---

## O que é

O OpenClaw suporta dois modos de autenticar com a OpenAI:

| Modo | Como funciona | Onde fica salvo |
|------|--------------|-----------------|
| **OAuth (Codex)** | Login via browser (ChatGPT account) | `~/.openclaw/agents/main/agent/auth-profiles.json` |
| **API Key** | Cola a chave `sk-...` | `~/.openclaw/.env` |

> OAuth não usa `.env`. Tokens OAuth ficam no `auth-profiles.json`.

---

## Como fazer o login OAuth

### Ambiente local (com browser)

```bash
openclaw onboard
# ou
openclaw models auth login openai-codex
```

O OpenClaw abre automaticamente `http://localhost:1455/auth/callback` no browser. Após o login, o token é gravado.

### Ambiente remoto / VPS / SSH (sem browser)

O OpenClaw detecta automaticamente ambientes headless pelas variáveis:

```
SSH_CLIENT / SSH_TTY / SSH_CONNECTION   → SSH
REMOTE_CONTAINERS / CODESPACES          → containers
Linux sem DISPLAY e sem WAYLAND_DISPLAY → servidor sem interface
```

Nesse caso, em vez de abrir o browser, ele **exibe a URL no terminal**:

```
Open this URL in your LOCAL browser:

https://auth.openai.com/oauth/authorize?...

Paste the redirect URL (or authorization code): _
```

Você abre no seu browser local, faz login, e cola o redirect URL de volta no terminal.

---

## Onde os tokens ficam gravados

### Arquivo principal

```
~/.openclaw/agents/main/agent/auth-profiles.json
```

Pode ser sobrescrito pela variável `OPENCLAW_AGENT_DIR` ou `PI_CODING_AGENT_DIR`.

### Estrutura do arquivo

```json
{
  "version": 1,
  "profiles": {
    "openai-codex:seu@email.com": {
      "type": "oauth",
      "provider": "openai-codex",
      "access": "<access_token>",
      "refresh": "<refresh_token>",
      "expires": 1740000000000,
      "email": "seu@email.com"
    }
  }
}
```

O profile ID segue o formato `openai-codex:<email>`. Se o email não for retornado no login, usa `openai-codex:default`.

### Arquivo legado (versões antigas)

```
~/.openclaw/agents/main/agent/auth.json
```

O OpenClaw ainda lê esse arquivo para compatibilidade retroativa.

---

## Como editar manualmente

### Trocar o access token

```bash
# 1. Abra o arquivo
nano ~/.openclaw/agents/main/agent/auth-profiles.json

# 2. Edite o campo "access" dentro do profile "openai-codex:seu@email.com"
# 3. Atualize o campo "expires" se necessário (timestamp em ms)
```

Calcule o timestamp de expiração:
```bash
# Expira em 1 hora a partir de agora
date -d "+1 hour" +%s%3N   # Linux
```

### Forçar re-login (apagar credenciais)

```bash
# Remove só o profile do Codex, mantém outros provedores
python3 -c "
import json, pathlib
p = pathlib.Path.home() / '.openclaw/agents/main/agent/auth-profiles.json'
data = json.loads(p.read_text())
data['profiles'] = {k: v for k, v in data['profiles'].items() if not k.startswith('openai-codex')}
p.write_text(json.dumps(data, indent=2))
print('Credenciais Codex removidas')
"

# Depois faça login novamente
openclaw models auth login openai-codex
```

### Verificar se o token está válido

```bash
python3 -c "
import json, time, pathlib
p = pathlib.Path.home() / '.openclaw/agents/main/agent/auth-profiles.json'
data = json.loads(p.read_text())
for pid, cred in data['profiles'].items():
    if 'openai-codex' in pid:
        exp = cred.get('expires', 0)
        left = (exp - time.time()*1000) / 60000
        status = f'válido por mais {left:.0f} min' if left > 0 else 'EXPIRADO'
        print(f'{pid}: {status}')
"
```

---

## Refresh automático de token

O OpenClaw renova o token automaticamente antes de cada chamada:

1. Verifica se `expires > Date.now()`
2. Se expirado, chama o endpoint de refresh com o `refresh_token`
3. Usa **file lock** para evitar race conditions quando múltiplos agentes rodam em paralelo
4. Se o refresh falhar, tenta herdar as credenciais do agente principal (`main`)
5. Se tudo falhar, lança erro pedindo re-autenticação

---

## Configuração no `openclaw.json`

Após o login, o OpenClaw registra o profile no arquivo de configuração:

```
~/.openclaw/openclaw.json
```

```json
{
  "auth": {
    "profiles": {
      "openai-codex:seu@email.com": {
        "provider": "openai-codex",
        "mode": "oauth"
      }
    }
  },
  "model": "openai-codex/codex-mini-latest"
}
```

---

## Variáveis de ambiente relevantes

| Variável | Efeito |
|----------|--------|
| `OPENCLAW_STATE_DIR` | Sobrescreve o diretório base (padrão: `~/.openclaw`) |
| `OPENCLAW_AGENT_DIR` | Sobrescreve o diretório do agente (padrão: `~/.openclaw/agents/main/agent`) |
| `PI_CODING_AGENT_DIR` | Alias de `OPENCLAW_AGENT_DIR` |

---

## Diferença entre OAuth e API Key no `.env`

O arquivo `~/.openclaw/.env` **só é usado para API Key**, nunca para OAuth:

```bash
# ~/.openclaw/.env  — só existe se você usou API key
OPENAI_API_KEY=sk-...
```

Esse arquivo existe por compatibilidade com o **launchd** (macOS), que não herda as variáveis de ambiente do shell ao iniciar o processo automaticamente. OAuth não precisa disso porque os tokens ficam no `auth-profiles.json`, que o OpenClaw lê diretamente.
