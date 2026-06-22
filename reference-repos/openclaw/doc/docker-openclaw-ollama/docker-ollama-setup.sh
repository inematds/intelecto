#!/usr/bin/env bash
set -euo pipefail

# OpenClaw + Ollama Docker Setup (Local Testing)
# Para testes locais com LLM via Ollama

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
IMAGE_NAME="${OPENCLAW_IMAGE:-openclaw:local}"
DEFAULT_MODEL="${OLLAMA_MODEL:-llama3.2}"

# OpenClaw source directory (for building Docker image)
OPENCLAW_SRC="${OPENCLAW_SRC:-$HOME/projetos/openclaw}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}==>${NC} $1"; }
log_success() { echo -e "${GREEN}==>${NC} $1"; }
log_warn() { echo -e "${YELLOW}==>${NC} $1"; }
log_error() { echo -e "${RED}==>${NC} $1" >&2; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log_error "Missing dependency: $1"
    exit 1
  fi
}

check_resources() {
  log_info "Checking system resources..."

  if [[ -f /proc/meminfo ]]; then
    local mem_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local mem_gb=$((mem_kb / 1024 / 1024))
    if [[ $mem_gb -lt 8 ]]; then
      log_warn "System has ${mem_gb}GB RAM. 8GB+ recommended."
      log_warn "Consider using smaller models (phi3, gemma2:2b)."
    else
      log_success "RAM: ${mem_gb}GB"
    fi
  fi
}

require_cmd docker
if ! docker compose version >/dev/null 2>&1; then
  log_error "Docker Compose not available"
  exit 1
fi

check_resources

# Configuration
OPENCLAW_CONFIG_DIR="${OPENCLAW_CONFIG_DIR:-$HOME/.openclaw}"
OPENCLAW_WORKSPACE_DIR="${OPENCLAW_WORKSPACE_DIR:-$HOME/.openclaw/workspace}"

mkdir -p "$OPENCLAW_CONFIG_DIR"
mkdir -p "$OPENCLAW_WORKSPACE_DIR"

export OPENCLAW_CONFIG_DIR
export OPENCLAW_WORKSPACE_DIR
export OPENCLAW_GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18789}"
export OPENCLAW_BRIDGE_PORT="${OPENCLAW_BRIDGE_PORT:-18790}"
export OPENCLAW_GATEWAY_BIND="${OPENCLAW_GATEWAY_BIND:-lan}"
export OPENCLAW_IMAGE="$IMAGE_NAME"
export OLLAMA_PORT="${OLLAMA_PORT:-11434}"
export OLLAMA_MEMORY_LIMIT="${OLLAMA_MEMORY_LIMIT:-8G}"

# Generate gateway token
if [[ -z "${OPENCLAW_GATEWAY_TOKEN:-}" ]]; then
  if command -v openssl >/dev/null 2>&1; then
    OPENCLAW_GATEWAY_TOKEN="$(openssl rand -hex 32)"
  else
    OPENCLAW_GATEWAY_TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  fi
fi
export OPENCLAW_GATEWAY_TOKEN

# Save .env
cat > "$ROOT_DIR/.env" <<EOF
OPENCLAW_CONFIG_DIR=$OPENCLAW_CONFIG_DIR
OPENCLAW_WORKSPACE_DIR=$OPENCLAW_WORKSPACE_DIR
OPENCLAW_GATEWAY_PORT=$OPENCLAW_GATEWAY_PORT
OPENCLAW_BRIDGE_PORT=$OPENCLAW_BRIDGE_PORT
OPENCLAW_GATEWAY_BIND=$OPENCLAW_GATEWAY_BIND
OPENCLAW_GATEWAY_TOKEN=$OPENCLAW_GATEWAY_TOKEN
OPENCLAW_IMAGE=$IMAGE_NAME
OLLAMA_PORT=$OLLAMA_PORT
OLLAMA_MEMORY_LIMIT=$OLLAMA_MEMORY_LIMIT
EOF

log_info "Building Docker image: $IMAGE_NAME from $OPENCLAW_SRC"
if [[ ! -d "$OPENCLAW_SRC" ]]; then
  log_error "OpenClaw source directory not found: $OPENCLAW_SRC"
  log_error "Set OPENCLAW_SRC environment variable to point to your openclaw repository"
  exit 1
fi
docker build -t "$IMAGE_NAME" -f "$OPENCLAW_SRC/Dockerfile" "$OPENCLAW_SRC"

log_info "Starting Ollama..."
docker compose -f "$COMPOSE_FILE" up -d ollama

log_info "Waiting for Ollama..."
max_attempts=30
attempt=0
while ! docker exec openclaw-ollama ollama list >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [[ $attempt -ge $max_attempts ]]; then
    log_error "Ollama failed to start"
    exit 1
  fi
  echo -n "."
  sleep 2
done
echo ""
log_success "Ollama ready"

log_info "Pulling model: $DEFAULT_MODEL..."
docker compose -f "$COMPOSE_FILE" exec -T ollama ollama pull "$DEFAULT_MODEL"
log_success "Model downloaded: $DEFAULT_MODEL"

# Create OpenClaw config for Ollama
OPENCLAW_CONFIG="$OPENCLAW_CONFIG_DIR/openclaw.json"
if [[ ! -f "$OPENCLAW_CONFIG" ]]; then
  log_info "Creating OpenClaw config for Ollama..."
  cat > "$OPENCLAW_CONFIG" <<JSON
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/$DEFAULT_MODEL"
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
            "id": "$DEFAULT_MODEL",
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
      "token": "$OPENCLAW_GATEWAY_TOKEN"
    }
  }
}
JSON
  log_success "Config created: $OPENCLAW_CONFIG"
else
  log_warn "Config exists: $OPENCLAW_CONFIG"
fi

log_info "Starting all services..."
docker compose -f "$COMPOSE_FILE" up -d

echo ""
log_success "Setup complete!"
echo ""
echo "Gateway: http://localhost:${OPENCLAW_GATEWAY_PORT}"
echo "Ollama:  http://localhost:${OLLAMA_PORT}"
echo "Token:   $OPENCLAW_GATEWAY_TOKEN"
echo "Model:   $DEFAULT_MODEL"
echo ""
echo "Commands:"
echo "  docker compose logs -f"
echo "  docker compose exec ollama ollama list"
echo "  docker compose exec ollama ollama pull mistral"
echo ""
echo "Test Ollama:"
echo "  curl http://localhost:${OLLAMA_PORT}/api/tags"
echo ""
