# OpenClaw - Setup Docker para VPS

## Requisitos

- Docker Engine + Docker Compose v2
- Git

## Deploy Rapido

### Opcao 1 - Script automatico (recomendado)

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
./docker-setup.sh
```

O script:
1. Builda a imagem Docker
2. Roda o wizard de onboarding (configuracao inicial)
3. Inicia o gateway via Docker Compose
4. Gera token de acesso e salva em `.env`

### Opcao 2 - Manual

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# Build da imagem
docker build -t openclaw:local -f Dockerfile .

# Onboarding (configuracao inicial)
docker compose run --rm openclaw-cli onboard

# Iniciar gateway
docker compose up -d openclaw-gateway
```

## Apos iniciar

- Acesse `http://IP-DA-VPS:18789/` no navegador
- Use o token gerado (salvo em `.env`) para autenticar na Control UI

## Portas

| Porta | Servico |
|-------|---------|
| 18789 | Gateway (API + UI) |
| 18790 | Bridge |

## Persistencia de dados

Os dados ficam em:
- `~/.openclaw/` - Configuracoes e sessoes
- `~/.openclaw/workspace` - Workspace dos agentes

## Configurar canais (opcional)

WhatsApp (QR):
```bash
docker compose run --rm openclaw-cli channels login
```

Telegram:
```bash
docker compose run --rm openclaw-cli channels add --channel telegram --token "<BOT_TOKEN>"
```

Discord:
```bash
docker compose run --rm openclaw-cli channels add --channel discord --token "<BOT_TOKEN>"
```

## Verificar saude

```bash
docker compose exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"
```

## Comandos uteis

```bash
# Ver logs
docker compose logs -f openclaw-gateway

# Parar
docker compose down

# Reiniciar
docker compose restart openclaw-gateway

# Atualizar
git pull
docker build -t openclaw:local -f Dockerfile .
docker compose up -d openclaw-gateway
```

## Seguranca para VPS

1. **Firewall** - Libere apenas as portas necessarias (18789, 22)
2. **HTTPS** - Use reverse proxy (nginx/caddy) com certificado SSL
3. **Token** - Mantenha o token do `.env` seguro

### Exemplo nginx reverse proxy

```nginx
server {
    listen 443 ssl;
    server_name seu-dominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Variaveis de ambiente opcionais

| Variavel | Descricao |
|----------|-----------|
| `OPENCLAW_DOCKER_APT_PACKAGES` | Pacotes apt extras para instalar na imagem |
| `OPENCLAW_EXTRA_MOUNTS` | Mounts adicionais (ex: `$HOME/.ssh:/home/node/.ssh:ro`) |
| `OPENCLAW_HOME_VOLUME` | Volume nomeado para persistir `/home/node` |

## Setup com Ollama (LLM local)

Para rodar modelos de IA localmente sem depender de APIs externas, use o setup com Ollama.

### Requisitos

- VPS com 8GB+ RAM (16GB recomendado)
- 40GB+ disco SSD
- Veja [requisitos-hardware-ollama.md](requisitos-hardware-ollama.md) para detalhes

### Deploy com Ollama

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
./docker-ollama-setup.sh
```

O script:
1. Verifica recursos do sistema
2. Builda a imagem OpenClaw
3. Inicia o Ollama
4. Baixa o modelo llama3.2 automaticamente
5. Configura OpenClaw para usar Ollama
6. Roda o wizard de onboarding
7. Inicia todos os servicos

### Setup manual com Ollama

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# Build da imagem
docker build -t openclaw:local -f Dockerfile .

# Iniciar com Ollama
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d

# Baixar modelo
docker compose -f docker-compose.yml -f docker-compose.ollama.yml exec ollama ollama pull llama3.2

# Onboarding
docker compose -f docker-compose.yml -f docker-compose.ollama.yml run --rm openclaw-cli onboard
```

### Configurar OpenClaw para Ollama

Crie ou edite `~/.openclaw/config.json5`:

```json5
{
  agents: {
    defaults: {
      model: { primary: "ollama/llama3.2" },
    },
  },
  models: {
    providers: {
      ollama: {
        baseUrl: "http://ollama:11434/v1",
        apiKey: "ollama-local",
      },
    },
  },
}
```

### Modelos recomendados

| RAM | Modelo | Comando |
|-----|--------|---------|
| 8 GB | llama3.2 (3B) | `ollama pull llama3.2` |
| 8 GB | phi3 (3.8B) | `ollama pull phi3` |
| 16 GB | mistral (7B) | `ollama pull mistral` |
| 16 GB | llama3.1:8b | `ollama pull llama3.1:8b` |

### Verificar Ollama

```bash
# Ver modelos disponiveis
docker compose -f docker-compose.yml -f docker-compose.ollama.yml exec ollama ollama list

# Testar API
curl http://localhost:11434/api/tags

# Ver uso de recursos
docker stats openclaw-ollama
```

### Trocar modelo

```bash
# Baixar novo modelo
docker compose -f docker-compose.yml -f docker-compose.ollama.yml exec ollama ollama pull mistral

# Editar config.json5 para usar o novo modelo
# model: { primary: "ollama/mistral" }
```

### Portas com Ollama

| Porta | Servico |
|-------|---------|
| 18789 | Gateway (API + UI) |
| 18790 | Bridge |
| 11434 | Ollama API |

## Documentacao completa

- Docker: https://docs.openclaw.ai/install/docker
- Hetzner VPS: https://docs.openclaw.ai/platforms/hetzner
- DigitalOcean: https://docs.openclaw.ai/platforms/digitalocean
- Requisitos Ollama: [requisitos-hardware-ollama.md](requisitos-hardware-ollama.md)
