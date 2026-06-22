#!/usr/bin/env bash
set -euo pipefail

# OpenClaw + Ollama Docker Setup
# Automated setup for self-hosted LLM deployment on VPS (8GB+ RAM recommended)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
OLLAMA_COMPOSE_FILE="$ROOT_DIR/docker-compose.ollama.yml"
EXTRA_COMPOSE_FILE="$ROOT_DIR/docker-compose.extra.yml"
IMAGE_NAME="${OPENCLAW_IMAGE:-openclaw:local}"
EXTRA_MOUNTS="${OPENCLAW_EXTRA_MOUNTS:-}"
HOME_VOLUME_NAME="${OPENCLAW_HOME_VOLUME:-}"
DEFAULT_MODEL="${OLLAMA_MODEL:-llama3.2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_system_resources() {
  log_info "Checking system resources..."

  # Check available memory
  local mem_kb
  if [[ -f /proc/meminfo ]]; then
    mem_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local mem_gb=$((mem_kb / 1024 / 1024))
    if [[ $mem_gb -lt 8 ]]; then
      log_warn "System has ${mem_gb}GB RAM. 8GB+ recommended for optimal performance."
      log_warn "Consider using smaller models (e.g., phi3, gemma2:2b) or adding swap."
    else
      log_success "System has ${mem_gb}GB RAM - sufficient for most models"
    fi
  fi

  # Check available disk space
  local disk_avail
  disk_avail=$(df -BG "$ROOT_DIR" | tail -1 | awk '{print $4}' | tr -d 'G')
  if [[ $disk_avail -lt 20 ]]; then
    log_warn "Low disk space: ${disk_avail}GB available. Models require 4-8GB each."
  else
    log_success "Disk space: ${disk_avail}GB available"
  fi
}

require_cmd docker
if ! docker compose version >/dev/null 2>&1; then
  log_error "Docker Compose not available (try: docker compose version)"
  exit 1
fi

check_system_resources

# Configuration directories
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
export OPENCLAW_DOCKER_APT_PACKAGES="${OPENCLAW_DOCKER_APT_PACKAGES:-}"
export OPENCLAW_EXTRA_MOUNTS="$EXTRA_MOUNTS"
export OPENCLAW_HOME_VOLUME="$HOME_VOLUME_NAME"
export OLLAMA_PORT="${OLLAMA_PORT:-11434}"

# Generate gateway token if not set
if [[ -z "${OPENCLAW_GATEWAY_TOKEN:-}" ]]; then
  if command -v openssl >/dev/null 2>&1; then
    OPENCLAW_GATEWAY_TOKEN="$(openssl rand -hex 32)"
  else
    OPENCLAW_GATEWAY_TOKEN="$(python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)"
  fi
fi
export OPENCLAW_GATEWAY_TOKEN

# Build compose files list
COMPOSE_FILES=("$COMPOSE_FILE" "$OLLAMA_COMPOSE_FILE")
COMPOSE_ARGS=()

# Handle extra mounts (same logic as docker-setup.sh)
write_extra_compose() {
  local home_volume="$1"
  shift
  local -a mounts=("$@")
  local mount

  cat >"$EXTRA_COMPOSE_FILE" <<'YAML'
services:
  openclaw-gateway:
    volumes:
YAML

  if [[ -n "$home_volume" ]]; then
    printf '      - %s:/home/node\n' "$home_volume" >>"$EXTRA_COMPOSE_FILE"
    printf '      - %s:/home/node/.openclaw\n' "$OPENCLAW_CONFIG_DIR" >>"$EXTRA_COMPOSE_FILE"
    printf '      - %s:/home/node/.openclaw/workspace\n' "$OPENCLAW_WORKSPACE_DIR" >>"$EXTRA_COMPOSE_FILE"
  fi

  for mount in "${mounts[@]}"; do
    printf '      - %s\n' "$mount" >>"$EXTRA_COMPOSE_FILE"
  done

  cat >>"$EXTRA_COMPOSE_FILE" <<'YAML'
  openclaw-cli:
    volumes:
YAML

  if [[ -n "$home_volume" ]]; then
    printf '      - %s:/home/node\n' "$home_volume" >>"$EXTRA_COMPOSE_FILE"
    printf '      - %s:/home/node/.openclaw\n' "$OPENCLAW_CONFIG_DIR" >>"$EXTRA_COMPOSE_FILE"
    printf '      - %s:/home/node/.openclaw/workspace\n' "$OPENCLAW_WORKSPACE_DIR" >>"$EXTRA_COMPOSE_FILE"
  fi

  for mount in "${mounts[@]}"; do
    printf '      - %s\n' "$mount" >>"$EXTRA_COMPOSE_FILE"
  done

  if [[ -n "$home_volume" && "$home_volume" != *"/"* ]]; then
    cat >>"$EXTRA_COMPOSE_FILE" <<YAML
volumes:
  ${home_volume}:
YAML
  fi
}

VALID_MOUNTS=()
if [[ -n "$EXTRA_MOUNTS" ]]; then
  IFS=',' read -r -a mounts <<<"$EXTRA_MOUNTS"
  for mount in "${mounts[@]}"; do
    mount="${mount#"${mount%%[![:space:]]*}"}"
    mount="${mount%"${mount##*[![:space:]]}"}"
    if [[ -n "$mount" ]]; then
      VALID_MOUNTS+=("$mount")
    fi
  done
fi

if [[ -n "$HOME_VOLUME_NAME" || ${#VALID_MOUNTS[@]} -gt 0 ]]; then
  write_extra_compose "$HOME_VOLUME_NAME" "${VALID_MOUNTS[@]}"
  COMPOSE_FILES+=("$EXTRA_COMPOSE_FILE")
fi

for compose_file in "${COMPOSE_FILES[@]}"; do
  COMPOSE_ARGS+=("-f" "$compose_file")
done

COMPOSE_HINT="docker compose"
for compose_file in "${COMPOSE_FILES[@]}"; do
  COMPOSE_HINT+=" -f ${compose_file}"
done

# Save environment to .env file
ENV_FILE="$ROOT_DIR/.env"
upsert_env() {
  local file="$1"
  shift
  local -a keys=("$@")
  local tmp
  tmp="$(mktemp)"
  declare -A seen=()

  if [[ -f "$file" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      local key="${line%%=*}"
      local replaced=false
      for k in "${keys[@]}"; do
        if [[ "$key" == "$k" ]]; then
          printf '%s=%s\n' "$k" "${!k-}" >>"$tmp"
          seen["$k"]=1
          replaced=true
          break
        fi
      done
      if [[ "$replaced" == false ]]; then
        printf '%s\n' "$line" >>"$tmp"
      fi
    done <"$file"
  fi

  for k in "${keys[@]}"; do
    if [[ -z "${seen[$k]:-}" ]]; then
      printf '%s=%s\n' "$k" "${!k-}" >>"$tmp"
    fi
  done

  mv "$tmp" "$file"
}

upsert_env "$ENV_FILE" \
  OPENCLAW_CONFIG_DIR \
  OPENCLAW_WORKSPACE_DIR \
  OPENCLAW_GATEWAY_PORT \
  OPENCLAW_BRIDGE_PORT \
  OPENCLAW_GATEWAY_BIND \
  OPENCLAW_GATEWAY_TOKEN \
  OPENCLAW_IMAGE \
  OPENCLAW_EXTRA_MOUNTS \
  OPENCLAW_HOME_VOLUME \
  OPENCLAW_DOCKER_APT_PACKAGES \
  OLLAMA_PORT

log_info "Building Docker image: $IMAGE_NAME"
docker build \
  --build-arg "OPENCLAW_DOCKER_APT_PACKAGES=${OPENCLAW_DOCKER_APT_PACKAGES}" \
  -t "$IMAGE_NAME" \
  -f "$ROOT_DIR/Dockerfile" \
  "$ROOT_DIR"

log_info "Starting Ollama service..."
docker compose "${COMPOSE_ARGS[@]}" up -d ollama

log_info "Waiting for Ollama to be ready..."
max_attempts=30
attempt=0
while ! docker compose "${COMPOSE_ARGS[@]}" exec -T ollama curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [[ $attempt -ge $max_attempts ]]; then
    log_error "Ollama failed to start after ${max_attempts} attempts"
    exit 1
  fi
  echo -n "."
  sleep 2
done
echo ""
log_success "Ollama is ready"

log_info "Pulling model: $DEFAULT_MODEL (this may take a few minutes)..."
docker compose "${COMPOSE_ARGS[@]}" exec -T ollama ollama pull "$DEFAULT_MODEL"
log_success "Model $DEFAULT_MODEL downloaded"

# Configure OpenClaw to use Ollama
OPENCLAW_CONFIG="$OPENCLAW_CONFIG_DIR/config.json5"
if [[ ! -f "$OPENCLAW_CONFIG" ]]; then
  log_info "Creating OpenClaw config for Ollama..."
  cat >"$OPENCLAW_CONFIG" <<JSON5
{
  agents: {
    defaults: {
      model: { primary: "ollama/${DEFAULT_MODEL}" },
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
JSON5
  log_success "Config created: $OPENCLAW_CONFIG"
else
  log_warn "Config already exists: $OPENCLAW_CONFIG"
  log_warn "You may need to manually configure Ollama provider. See doc/docker-vps-setup.md"
fi

echo ""
log_info "Onboarding (interactive)"
echo "When prompted:"
echo "  - Gateway bind: lan"
echo "  - Gateway auth: token"
echo "  - Gateway token: $OPENCLAW_GATEWAY_TOKEN"
echo "  - Tailscale exposure: Off"
echo "  - Install Gateway daemon: No"
echo ""
docker compose "${COMPOSE_ARGS[@]}" run --rm openclaw-cli onboard --no-install-daemon

log_info "Starting all services..."
docker compose "${COMPOSE_ARGS[@]}" up -d

echo ""
log_success "Setup complete!"
echo ""
echo "Services running:"
echo "  - Gateway: http://localhost:${OPENCLAW_GATEWAY_PORT}"
echo "  - Ollama:  http://localhost:${OLLAMA_PORT}"
echo ""
echo "Model: $DEFAULT_MODEL"
echo "Token: $OPENCLAW_GATEWAY_TOKEN"
echo ""
echo "Config: $OPENCLAW_CONFIG_DIR"
echo "Workspace: $OPENCLAW_WORKSPACE_DIR"
echo ""
echo "Commands:"
echo "  ${COMPOSE_HINT} logs -f"
echo "  ${COMPOSE_HINT} ps"
echo "  ${COMPOSE_HINT} exec ollama ollama list"
echo "  ${COMPOSE_HINT} exec ollama ollama pull mistral"
echo ""
echo "Verification:"
echo "  curl http://localhost:${OLLAMA_PORT}/api/tags"
echo "  curl http://localhost:${OPENCLAW_GATEWAY_PORT}/health"
echo ""
