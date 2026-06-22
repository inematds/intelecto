#!/usr/bin/env bash
set -euo pipefail

# OpenClaw + OpenRouter Docker Setup
# Para deploy em VPS com Claude Sonnet via OpenRouter

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
IMAGE_NAME="${OPENCLAW_IMAGE:-openclaw:local}"

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

require_cmd docker
if ! docker compose version >/dev/null 2>&1; then
  log_error "Docker Compose not available"
  exit 1
fi

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

# Generate gateway token
if [[ -z "${OPENCLAW_GATEWAY_TOKEN:-}" ]]; then
  if command -v openssl >/dev/null 2>&1; then
    OPENCLAW_GATEWAY_TOKEN="$(openssl rand -hex 32)"
  else
    OPENCLAW_GATEWAY_TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  fi
fi
export OPENCLAW_GATEWAY_TOKEN

# Prompt for OpenRouter API key
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo ""
  read -p "OpenRouter API Key: " OPENROUTER_API_KEY
fi

# Save .env
cat > "$ROOT_DIR/.env" <<EOF
OPENCLAW_CONFIG_DIR=$OPENCLAW_CONFIG_DIR
OPENCLAW_WORKSPACE_DIR=$OPENCLAW_WORKSPACE_DIR
OPENCLAW_GATEWAY_PORT=$OPENCLAW_GATEWAY_PORT
OPENCLAW_BRIDGE_PORT=$OPENCLAW_BRIDGE_PORT
OPENCLAW_GATEWAY_BIND=$OPENCLAW_GATEWAY_BIND
OPENCLAW_GATEWAY_TOKEN=$OPENCLAW_GATEWAY_TOKEN
OPENCLAW_IMAGE=$IMAGE_NAME
EOF

log_info "Building Docker image: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" -f "$ROOT_DIR/Dockerfile" "$ROOT_DIR"

# Create OpenClaw config for OpenRouter
OPENCLAW_CONFIG="$OPENCLAW_CONFIG_DIR/openclaw.json"
if [[ ! -f "$OPENCLAW_CONFIG" ]]; then
  log_info "Creating OpenClaw config for OpenRouter..."
  cat > "$OPENCLAW_CONFIG" <<JSON
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
        "apiKey": "$OPENROUTER_API_KEY",
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
      "token": "$OPENCLAW_GATEWAY_TOKEN"
    }
  }
}
JSON
  log_success "Config created: $OPENCLAW_CONFIG"
else
  log_warn "Config exists: $OPENCLAW_CONFIG"
fi

log_info "Starting gateway..."
docker compose -f "$COMPOSE_FILE" up -d

echo ""
log_success "Setup complete!"
echo ""
echo "Gateway: http://localhost:${OPENCLAW_GATEWAY_PORT}"
echo "Token: $OPENCLAW_GATEWAY_TOKEN"
echo "Model: Claude Sonnet 4 (via OpenRouter)"
echo ""
echo "Commands:"
echo "  docker compose logs -f"
echo "  docker compose ps"
echo ""
