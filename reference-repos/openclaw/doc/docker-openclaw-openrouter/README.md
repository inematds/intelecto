# OpenClaw + OpenRouter (Docker)

Setup Docker para rodar OpenClaw com Claude Sonnet 4 via OpenRouter.

Ideal para producao em VPS sem GPU.

## Requisitos

- Docker Engine + Docker Compose v2
- Chave API do OpenRouter (https://openrouter.ai)
- VPS com 2GB+ RAM

## Quick Start

```bash
# Clonar OpenClaw
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# Rodar setup (vai pedir a API key)
./doc/docker-openclaw-openrouter/docker-openrouter-setup.sh
```

## Acessar

Apos o setup, acesse:

```
http://<IP-VPS>:18789/?token=<TOKEN>
```

O token e exibido no final do setup.

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                      VPS                             │
│                                                      │
│  ┌──────────────────────┐                           │
│  │  OpenClaw Gateway    │◄────► OpenRouter API      │
│  │  :18789              │       (Claude Sonnet 4)   │
│  └──────────────────────┘                           │
│              ▲                                       │
└──────────────┼───────────────────────────────────────┘
               │
         ~/.openclaw
         (config)
```

## Configuracao

O setup cria `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "openrouter/anthropic/claude-sonnet-4"
      }
    }
  },
  "models": {
    "providers": {
      "openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1",
        "apiKey": "<OPENROUTER_API_KEY>",
        "api": "openai-completions",
        "models": [
          {
            "id": "anthropic/claude-sonnet-4",
            "name": "Claude Sonnet 4",
            "reasoning": false,
            "input": ["text", "image"],
            "cost": {
              "input": 3,
              "output": 15,
              "cacheRead": 0.3,
              "cacheWrite": 3.75
            },
            "contextWindow": 200000,
            "maxTokens": 16000
          }
        ]
      }
    }
  },
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "dangerouslyDisableDeviceAuth": true
    },
    "auth": {
      "mode": "token",
      "token": "<TOKEN>"
    }
  }
}
```

## Modelos Disponiveis

Via OpenRouter voce pode usar varios modelos. Altere `agents.defaults.model.primary`:

| Modelo | ID | Custo (por 1M tokens) |
|--------|----|-----------------------|
| Claude Sonnet 4 | anthropic/claude-sonnet-4 | $3 in / $15 out |
| Claude Opus 4 | anthropic/claude-opus-4 | $15 in / $75 out |
| GPT-4o | openai/gpt-4o | $2.5 in / $10 out |
| Llama 3.1 405B | meta-llama/llama-3.1-405b | $2 in / $2 out |

Para adicionar um modelo, inclua na lista `models` do provider:

```json
{
  "id": "openai/gpt-4o",
  "name": "GPT-4o",
  "reasoning": false,
  "input": ["text", "image"],
  "cost": { "input": 2.5, "output": 10, "cacheRead": 0, "cacheWrite": 0 },
  "contextWindow": 128000,
  "maxTokens": 16000
}
```

## Portas

| Porta | Servico | Descricao |
|-------|---------|-----------|
| 18789 | Gateway | Web UI + WebSocket |
| 18790 | Bridge | Bridge connections |

## Comandos Uteis

```bash
# Ver logs
docker compose logs -f

# Status
docker compose ps

# Parar
docker compose down

# Reiniciar
docker compose restart openclaw-gateway
```

## Variaveis de Ambiente

| Variavel | Default | Descricao |
|----------|---------|-----------|
| OPENROUTER_API_KEY | - | Chave API do OpenRouter |
| OPENCLAW_CONFIG_DIR | ~/.openclaw | Diretorio de config |
| OPENCLAW_GATEWAY_PORT | 18789 | Porta do gateway |
| OPENCLAW_GATEWAY_BIND | lan | Bind (lan/loopback) |

## Seguranca em Producao

Para expor na internet:

1. **Use HTTPS** - Configure reverse proxy (nginx/caddy) com SSL
2. **Firewall** - Libere apenas portas necessarias
3. **Token forte** - Use token gerado automaticamente (64 chars)

Exemplo nginx:

```nginx
server {
    listen 443 ssl;
    server_name openclaw.exemplo.com;

    ssl_certificate /etc/letsencrypt/live/openclaw.exemplo.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openclaw.exemplo.com/privkey.pem;

    location / {
        proxy_pass http://localhost:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### "pairing required"

Adicione na config:

```json
"controlUi": {
  "dangerouslyDisableDeviceAuth": true
}
```

### Timeout nas respostas

OpenRouter pode ter latencia. Verifique:
- Status do OpenRouter: https://status.openrouter.ai
- Creditos na conta

### Gateway nao inicia

Verifique `gateway.mode: "local"`:

```bash
cat ~/.openclaw/openclaw.json | grep -A2 gateway
```
