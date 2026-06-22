# OpenClaw + Ollama (Docker)

Setup Docker para rodar OpenClaw com Ollama localmente.

## Requisitos

- Docker Engine + Docker Compose v2
- 8GB+ RAM (16GB recomendado)
- GPU NVIDIA (opcional, mas recomendado para performance)

## Quick Start

```bash
# Clonar OpenClaw
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# Rodar setup
./doc/docker-openclaw-ollama/docker-ollama-setup.sh
```

Ou se o OpenClaw ja estiver clonado:

```bash
cd ~/projetos/openclaw-ollama-local
OPENCLAW_SRC=~/projetos/openclaw ./docker-ollama-setup.sh
```

## Acessar

Apos o setup, acesse:

```
http://localhost:18789/?token=<TOKEN>
```

O token e exibido no final do setup.

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    Docker Network                    │
│                                                      │
│  ┌──────────────┐         ┌──────────────────────┐  │
│  │    Ollama    │◄───────►│  OpenClaw Gateway    │  │
│  │  :11434      │         │  :18789              │  │
│  │  (GPU/CPU)   │         │                      │  │
│  └──────────────┘         └──────────────────────┘  │
│         ▲                          ▲                │
└─────────┼──────────────────────────┼────────────────┘
          │                          │
    ollama-data               ~/.openclaw
    (modelos)                 (config)
```

## GPU vs CPU

### Com GPU NVIDIA

O docker-compose.yml ja esta configurado para usar GPU:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

Verificar se GPU esta sendo usada:

```bash
# Ver uso da GPU
nvidia-smi

# Ver se Ollama esta usando GPU
docker compose exec ollama ollama ps
# Deve mostrar "100% GPU"
```

### Sem GPU (CPU only)

Remova a secao `deploy.resources.reservations` do docker-compose.yml.

**Aviso:** Inferencia em CPU e muito lenta (30-60s por resposta). Para producao sem GPU, use OpenRouter.

## Modelos Recomendados

| RAM | GPU VRAM | Modelo | Comando |
|-----|----------|--------|---------|
| 8GB | 4GB | llama3.2 (3B) | `ollama pull llama3.2` |
| 16GB | 8GB | mistral (7B) | `ollama pull mistral` |
| 16GB | 8GB | llama3.1:8b | `ollama pull llama3.1:8b` |
| 32GB | 16GB | llama3.1:70b | `ollama pull llama3.1:70b` |

```bash
# Baixar modelo adicional
docker compose exec ollama ollama pull mistral

# Listar modelos instalados
docker compose exec ollama ollama list
```

## Portas

| Porta | Servico | Descricao |
|-------|---------|-----------|
| 18789 | Gateway | Web UI + WebSocket |
| 18790 | Bridge | Bridge connections |
| 11434 | Ollama | API LLM |

## Configuracao

O setup cria `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/llama3.2"
      }
    }
  },
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://ollama:11434/v1",
        "apiKey": "ollama-local",
        "api": "openai-completions",
        "models": [
          {
            "id": "llama3.2",
            "name": "Llama 3.2",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 32768,
            "maxTokens": 4096
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

### Trocar modelo padrao

Edite `~/.openclaw/openclaw.json`:

```json
"primary": "ollama/mistral"
```

E reinicie o gateway:

```bash
docker compose restart openclaw-gateway
```

## Comandos Uteis

```bash
# Ver logs
docker compose logs -f

# Ver logs do gateway
docker compose logs -f openclaw-gateway

# Ver logs do Ollama
docker compose logs -f ollama

# Status dos containers
docker compose ps

# Parar tudo
docker compose down

# Parar e remover volumes (apaga modelos!)
docker compose down -v

# Reiniciar gateway
docker compose restart openclaw-gateway

# Testar Ollama diretamente
curl http://localhost:11434/api/tags

# Testar geracao
docker compose exec ollama ollama run llama3.2 "Ola!"
```

## Troubleshooting

### "pairing required" ou "disconnected (1008)"

Verifique se a config tem:

```json
"controlUi": {
  "dangerouslyDisableDeviceAuth": true
}
```

### "context window too small"

OpenClaw requer minimo 16000 tokens de context. Verifique:

```json
"contextWindow": 32768
```

### Ollama nao usa GPU

1. Verifique drivers NVIDIA: `nvidia-smi`
2. Verifique se container tem acesso: `docker compose exec ollama nvidia-smi`
3. Recrie container: `docker compose up -d --force-recreate ollama`

### Inferencia muito lenta

- Em CPU: esperado (30-60s por resposta)
- Em GPU: verifique se modelo cabe na VRAM
- Use modelos menores: llama3.2 (3B), phi3, gemma2:2b

### Gateway nao inicia

Verifique se `gateway.mode: "local"` esta na config:

```bash
cat ~/.openclaw/openclaw.json | grep -A2 gateway
```

## Variaveis de Ambiente

| Variavel | Default | Descricao |
|----------|---------|-----------|
| OPENCLAW_SRC | ~/projetos/openclaw | Diretorio do source OpenClaw |
| OPENCLAW_CONFIG_DIR | ~/.openclaw | Diretorio de config |
| OPENCLAW_GATEWAY_PORT | 18789 | Porta do gateway |
| OPENCLAW_BRIDGE_PORT | 18790 | Porta do bridge |
| OLLAMA_PORT | 11434 | Porta do Ollama |
| OLLAMA_MODEL | llama3.2 | Modelo padrao |
| OLLAMA_MEMORY_LIMIT | 8G | Limite de memoria (sem GPU) |

## Seguranca

Este setup usa `dangerouslyDisableDeviceAuth: true` para facilitar testes locais. **NAO use em producao exposta na internet.**

Para producao:
- Use HTTPS (certificado SSL)
- Remova `dangerouslyDisableDeviceAuth`
- Configure pairing de dispositivos
- Use allowlists

## Modelos Testados

Veja [MODELOS-TESTADOS.md](MODELOS-TESTADOS.md) para documentacao completa dos modelos testados, problemas encontrados e recomendacoes.

### Resumo Rapido

| Modelo | Provider | Status | Recomendado |
|--------|----------|--------|-------------|
| qwen2.5:32b | Ollama | Funciona | **Sim (local)** |
| Qwen3 Coder 480B | OpenRouter | Funciona | **Sim (free)** |
| Llama 3.3 70B | OpenRouter | Funciona | Sim (free) |
| Claude Sonnet 4 | OpenRouter | Funciona | Sim (pago) |
| llama3.2, llama3.1:8b | Ollama | Funciona | Nao (qualidade baixa) |
| deepseek-r1 | Ollama | Nao funciona | Nao (incompativel) |
| llama3.1:70b | Ollama | Muito lento | Nao |

### Recomendacoes

**Para uso local (Ollama):**
- `qwen2.5:32b` - Melhor portugues, 19GB

**Para uso via API (OpenRouter - Gratuito):**
- `qwen/qwen3-coder:free` - 480B MoE, otimizado para codigo
- `meta-llama/llama-3.3-70b-instruct:free` - Bom geral

**Para uso via API (OpenRouter - Pago):**
- `anthropic/claude-sonnet-4` - Melhor qualidade
