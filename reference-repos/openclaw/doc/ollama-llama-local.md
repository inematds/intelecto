# OpenClaw - Usando Llama Local com Ollama

## O que e Ollama?

Ollama e um runtime local para LLMs que permite rodar modelos open-source (Llama, Qwen, DeepSeek, Mistral, etc.) na sua propria maquina. O OpenClaw integra nativamente com a API do Ollama.

## Instalacao do Ollama

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### macOS
```bash
brew install ollama
```

### Windows
Baixe o instalador em: https://ollama.ai/download

## Baixar modelos

```bash
# Llama 3.3 (recomendado para uso geral)
ollama pull llama3.3

# Qwen 2.5 Coder (bom para codigo)
ollama pull qwen2.5-coder:32b

# DeepSeek R1 (modelo de raciocinio)
ollama pull deepseek-r1:32b

# Mistral
ollama pull mistral

# Ver modelos instalados
ollama list
```

## Configurar no OpenClaw

### Opcao 1 - Variavel de ambiente (mais simples)

```bash
export OLLAMA_API_KEY="ollama-local"
```

O OpenClaw auto-descobre modelos que suportam tools.

### Opcao 2 - Comando de config

```bash
openclaw config set models.providers.ollama.apiKey "ollama-local"
```

### Opcao 3 - Arquivo de configuracao

Edite `~/.openclaw/config.json5`:

```json5
{
  agents: {
    defaults: {
      model: { primary: "ollama/llama3.3" },
    },
  },
}
```

## Configuracao avancada

### Ollama em outro host/porta

Se o Ollama roda em outra maquina:

```json5
{
  models: {
    providers: {
      ollama: {
        baseUrl: "http://192.168.1.100:11434/v1",
        apiKey: "ollama-local",
        api: "openai-completions",
        models: [
          {
            id: "llama3.3",
            name: "Llama 3.3",
            reasoning: false,
            input: ["text"],
            cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
            contextWindow: 8192,
            maxTokens: 81920
          }
        ]
      }
    }
  }
}
```

### Modelo principal local + fallback na nuvem

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "ollama/llama3.3",
        fallback: ["anthropic/claude-sonnet-4-5"],
      },
    },
  },
  models: {
    mode: "merge",  // Mantem modelos da nuvem disponiveis
  },
}
```

### Modelo da nuvem + fallback local

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-sonnet-4-5",
        fallback: ["ollama/llama3.3"],
      },
    },
  },
  models: {
    mode: "merge",
  },
}
```

## Comandos uteis

```bash
# Iniciar Ollama (se nao estiver rodando)
ollama serve

# Listar modelos instalados
ollama list

# Listar modelos disponiveis no OpenClaw
openclaw models list

# Baixar novo modelo
ollama pull <nome-do-modelo>

# Remover modelo
ollama rm <nome-do-modelo>

# Testar API
curl http://localhost:11434/api/tags
```

## Modelos recomendados

| Modelo | Uso | RAM necessaria |
|--------|-----|----------------|
| llama3.3 | Uso geral | ~8GB |
| qwen2.5-coder:32b | Codigo | ~20GB |
| deepseek-r1:32b | Raciocinio | ~20GB |
| mistral | Leve/rapido | ~5GB |
| codellama | Codigo | ~8GB |

## Consideracoes de hardware

### Minimo
- 8GB RAM para modelos pequenos (7B)
- CPU moderna

### Recomendado
- 16-32GB RAM
- GPU com 8GB+ VRAM (NVIDIA recomendado)

### Ideal (para modelos grandes)
- 64GB+ RAM
- GPU com 24GB+ VRAM
- Ou Mac com Apple Silicon (M1/M2/M3 com 32GB+)

## Usando no Docker

Se o OpenClaw roda em Docker e o Ollama no host:

```json5
{
  models: {
    providers: {
      ollama: {
        // host.docker.internal aponta para o host
        baseUrl: "http://host.docker.internal:11434/v1",
        apiKey: "ollama-local",
      },
    },
  },
}
```

No docker-compose, adicione:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

## Troubleshooting

### Ollama nao detectado
```bash
# Verificar se esta rodando
ps aux | grep ollama

# Iniciar
ollama serve

# Testar API
curl http://localhost:11434/api/tags
```

### Modelo nao aparece no OpenClaw
O OpenClaw so descobre modelos com suporte a tools. Defina manualmente se necessario:
```bash
openclaw config set models.providers.ollama.models '[{"id":"seu-modelo","name":"Seu Modelo"}]'
```

### Lentidao
- Use modelos menores
- Verifique se GPU esta sendo usada
- Aumente RAM disponivel

### Erro de conexao no Docker
Use `host.docker.internal` em vez de `localhost`

## Alternativas ao Ollama

O OpenClaw tambem suporta:

- **LM Studio** - Interface grafica, facil de usar
- **vLLM** - Alto desempenho, melhor para producao
- **LiteLLM** - Proxy unificado para varios backends

Todos funcionam via API compativel com OpenAI.

## Documentacao oficial

- Ollama: https://ollama.ai
- OpenClaw Ollama: https://docs.openclaw.ai/providers/ollama
- OpenClaw Local Models: https://docs.openclaw.ai/gateway/local-models
