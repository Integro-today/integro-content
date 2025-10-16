#!/usr/bin/env bash

set -euo pipefail

# ==============================================================================
# Integro Agents - One-shot deployment script for Ubuntu 24.04 droplet
# - Installs prerequisites (Python 3, Node.js, Docker, Caddy)
# - Sets up local Qdrant via Docker
# - Clones/updates app repo and installs backend deps
# - Builds Next.js frontend
# - Configures systemd services for backend and frontend
# - Configures Caddy for domain TLS and reverse proxy
# NOTE: This script does NOT configure any firewall rules.
# Run as root on the droplet.
# ==============================================================================

# ------------------------------ Configuration ---------------------------------
# Allow overrides via environment variables
DOMAIN="${DOMAIN:-xarov.com}"
APP_DIR="${APP_DIR:-/opt/integro-agents}"
REPO_URL="${REPO_URL:-}"  # e.g. https://github.com/your-org/integro-agents.git (leave empty if already present at APP_DIR)

# Basic auth for frontend (Caddy basicauth)
BASIC_AUTH_USER="${BASIC_AUTH_USER:-integro}"
BASIC_AUTH_PASSWORD="${BASIC_AUTH_PASSWORD:-gointegro}"

# Ports (internal, bound to localhost)
BACKEND_PORT="${BACKEND_PORT:-8888}"
FRONTEND_PORT="${FRONTEND_PORT:-8889}"
QDRANT_PORT="${QDRANT_PORT:-6333}"

# Systemd unit names
BACKEND_UNIT="${BACKEND_UNIT:-integro-backend.service}"
FRONTEND_UNIT="${FRONTEND_UNIT:-integro-frontend.service}"
VOICE_AGENT_UNIT="${VOICE_AGENT_UNIT:-integro-voice-agent.service}"
QDRANT_DOCKER_UNIT="${QDRANT_DOCKER_UNIT:-qdrant-docker.service}"

# Node version setup script
NODESOURCE_SETUP="${NODESOURCE_SETUP:-https://deb.nodesource.com/setup_20.x}"

# ------------------------------------------------------------------------------

log() {
  echo "[deploy] $*"
}

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "This script must be run as root." >&2
    exit 1
  fi
}

install_prereqs() {
  export DEBIAN_FRONTEND=noninteractive
  log "Installing prerequisites (build chain, Python 3, Node.js, Docker, Caddy, voice agent deps)"

  apt-get update -y
  apt-get install -y ca-certificates curl gnupg lsb-release build-essential git \
    python3 python3-venv python3-dev pkg-config gcc g++ \
    libva-drm2 libva2

  # Node.js 20 LTS
  if ! command -v node >/dev/null 2>&1; then
    curl -fsSL "$NODESOURCE_SETUP" | bash -
    apt-get install -y nodejs
  fi

  # Docker (for Qdrant)
  if ! command -v docker >/dev/null 2>&1; then
    apt-get install -y docker.io
    systemctl enable --now docker
  fi

  # Caddy (official repo)
  if ! command -v caddy >/dev/null 2>&1; then
    apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key | \
      gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt | \
      tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
    apt-get update -y
    apt-get install -y caddy
  fi
}

prepare_directories() {
  log "Preparing application and data directories"
  mkdir -p "$APP_DIR" /var/lib/qdrant
  chmod 755 "$APP_DIR" /var/lib/qdrant
}

clone_or_update_repo() {
  if [[ -d "$APP_DIR/.git" ]]; then
    log "Repository exists. Pulling latest changes."
    git -C "$APP_DIR" fetch --all --prune
    git -C "$APP_DIR" pull --rebase || true
  else
    if [[ -n "${REPO_URL}" ]]; then
      log "Cloning repository: $REPO_URL"
      git clone "$REPO_URL" "$APP_DIR"
    else
      log "No repo found at $APP_DIR and REPO_URL is empty. Assuming code already present (e.g., rsynced)."
    fi
  fi
}

setup_python_backend() {
  log "Setting up Python virtual environment and backend dependencies"
  cd "$APP_DIR"
  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --upgrade pip
  if [[ -f requirements.txt ]]; then
    pip install -r requirements.txt
  fi
  # Install editable package if setup.py/pyproject present
  if [[ -f setup.py || -f pyproject.toml ]]; then
    pip install -e .
  fi
  deactivate
}

ensure_env_file() {
  log "Ensuring .env contains required keys (will not override existing values)"
  local env_file="$APP_DIR/.env"
  touch "$env_file"
  chmod 600 "$env_file"

  # Add FRONTEND_ORIGIN if missing
  if ! grep -q '^FRONTEND_ORIGIN=' "$env_file"; then
    echo "FRONTEND_ORIGIN=https://$DOMAIN" >> "$env_file"
  fi
  # Add QDRANT_URL if missing
  if ! grep -q '^QDRANT_URL=' "$env_file"; then
    echo "QDRANT_URL=http://127.0.0.1:$QDRANT_PORT" >> "$env_file"
  fi
  # Add voice agent environment defaults if missing
  if ! grep -q '^LIVEKIT_URL=' "$env_file"; then
    echo "# LIVEKIT_URL=wss://your-project.livekit.cloud" >> "$env_file"
  fi
  if ! grep -q '^CARTESIA_MODEL=' "$env_file"; then
    echo "CARTESIA_MODEL=sonic-2" >> "$env_file"
  fi
  if ! grep -q '^CARTESIA_VOICE_ID=' "$env_file"; then
    echo "CARTESIA_VOICE_ID=00a77add-48d5-4ef6-8157-71e5437b282d" >> "$env_file"
  fi
  # DATABASE_URL expected to be provided already by operator; do not overwrite.
  # Voice agent API keys (LIVEKIT_API_KEY, LIVEKIT_API_SECRET, ASSEMBLYAI_API_KEY, CARTESIA_API_KEY) 
  # should be provided by operator in .env file
}

start_qdrant_container() {
  log "Starting Qdrant container (bound to localhost)"
  if docker ps -a --format '{{.Names}}' | grep -q '^qdrant$'; then
    log "Qdrant container already exists. Ensuring it is running."
    docker start qdrant >/dev/null || true
  else
    docker run -d --name qdrant --restart unless-stopped \
      -p 127.0.0.1:"$QDRANT_PORT":6333 \
      -v /var/lib/qdrant:/qdrant/storage \
      qdrant/qdrant:latest >/dev/null
  fi

  # Create a simple systemd wrapper to manage the container
  cat > "/etc/systemd/system/$QDRANT_DOCKER_UNIT" <<EOF
[Unit]
Description=Qdrant via Docker
After=network-online.target docker.service
Requires=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker start -a qdrant
ExecStop=/usr/bin/docker stop -t 10 qdrant

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now "$QDRANT_DOCKER_UNIT"
}

setup_frontend_deps() {
  log "Installing frontend dependencies (dev server mode)"
  cd "$APP_DIR/frontend"
  
  # Clean any existing build artifacts that could interfere with dev server
  if [[ -d .next ]]; then
    log "Removing existing .next build directory for clean dev server start"
    rm -rf .next
  fi
  
  # Install dependencies
  if command -v npm >/dev/null 2>&1; then
    if [[ -f package-lock.json ]]; then
      npm ci
    else
      npm install
    fi
  else
    log "npm not found; Node.js installation likely failed"
    exit 1
  fi
}

write_systemd_units() {
  log "Writing systemd units for backend, frontend, and voice agent"
  # Backend
  cat > "/etc/systemd/system/$BACKEND_UNIT" <<EOF
[Unit]
Description=Integro FastAPI backend
After=network-online.target $QDRANT_DOCKER_UNIT
Wants=$QDRANT_DOCKER_UNIT

[Service]
Type=simple
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn integro.web_server:app --host 127.0.0.1 --port $BACKEND_PORT --workers 1
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

  # Frontend (Next.js dev server)
  cat > "/etc/systemd/system/$FRONTEND_UNIT" <<EOF
[Unit]
Description=Integro Next.js frontend (dev server)
After=network-online.target $BACKEND_UNIT

[Service]
Type=simple
WorkingDirectory=$APP_DIR/frontend
Environment=PORT=$FRONTEND_PORT
Environment=NEXT_PUBLIC_API_BASE_URL=https://$DOMAIN
Environment=NODE_ENV=development
ExecStart=/usr/bin/npm run dev -- --port $FRONTEND_PORT --hostname 127.0.0.1
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

  # Voice Agent
  cat > "/etc/systemd/system/$VOICE_AGENT_UNIT" <<EOF
[Unit]
Description=Integro Voice Agent (LiveKit)
After=network-online.target $BACKEND_UNIT $QDRANT_DOCKER_UNIT
Wants=$BACKEND_UNIT $QDRANT_DOCKER_UNIT

[Service]
Type=simple
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
Environment=PYTHONUNBUFFERED=1
Environment=TOKENIZERS_PARALLELISM=false
Environment=CUDA_VISIBLE_DEVICES=-1
Environment=LLAMA_CPU=true
Environment=PYTORCH_ENABLE_MPS_FALLBACK=1
ExecStart=$APP_DIR/.venv/bin/python scripts/run_voice_agent.py dev
Restart=always
RestartSec=10
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  
  # Stop services if they're running to ensure clean restart
  systemctl stop "$FRONTEND_UNIT" 2>/dev/null || true
  systemctl stop "$VOICE_AGENT_UNIT" 2>/dev/null || true
  
  systemctl enable --now "$BACKEND_UNIT"
  systemctl enable --now "$FRONTEND_UNIT"
  systemctl enable --now "$VOICE_AGENT_UNIT"
}

write_caddyfile() {
  log "Configuring Caddy for $DOMAIN"
  local caddyfile="/etc/caddy/Caddyfile"
  # Hash the basic auth password using Caddy's helper (bcrypt)
  local BASIC_AUTH_HASH
  BASIC_AUTH_HASH="$(caddy hash-password --plaintext "$BASIC_AUTH_PASSWORD")"
  if [[ -f "$caddyfile" ]]; then
    cp "$caddyfile" "/etc/caddy/Caddyfile.bak.$(date +%s)"
  fi
  cat > "$caddyfile" <<EOF
$DOMAIN {
  encode gzip zstd

  # Require basic auth for all non-API/non-WS paths (protects frontend UI)
  @frontend not path /api* /health* /health/detailed /ws* /ws/multi-agent*
  basic_auth @frontend {
    $BASIC_AUTH_USER $BASIC_AUTH_HASH
  }

  @api path /api* /health* /health/detailed
  reverse_proxy @api 127.0.0.1:$BACKEND_PORT

  @ws path /ws* /ws/multi-agent*
  reverse_proxy @ws 127.0.0.1:$BACKEND_PORT

  # Frontend Next.js server
  reverse_proxy 127.0.0.1:$FRONTEND_PORT
}

www.$DOMAIN {
  redir https://$DOMAIN{uri} permanent
}
EOF
  caddy validate --config "$caddyfile"
  systemctl reload caddy || systemctl restart caddy
  systemctl enable --now caddy
}

verify_services() {
  log "Verifying local health endpoints and service status"
  set +e
  
  # Check backend health
  curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" || true
  
  # Wait a moment for services to fully start
  sleep 5
  
  # Check frontend dev server is responding
  log "Checking frontend dev server..."
  curl -fsS "http://127.0.0.1:$FRONTEND_PORT/" -o /dev/null || {
    log "Frontend dev server not responding. Checking service status..."
    systemctl status "$FRONTEND_UNIT" --no-pager || true
  }
  
  # Check voice agent service status
  log "Checking voice agent service status..."
  systemctl status "$VOICE_AGENT_UNIT" --no-pager || {
    log "Voice agent service not running properly. Check logs with: journalctl -u $VOICE_AGENT_UNIT -f"
  }
  
  set -e
}

main() {
  require_root
  install_prereqs
  prepare_directories
  clone_or_update_repo
  setup_python_backend
  ensure_env_file
  start_qdrant_container
  setup_frontend_deps
  write_systemd_units
  write_caddyfile
  verify_services
  log "Deployment completed. Visit: https://$DOMAIN"
  log "Voice agent service: $VOICE_AGENT_UNIT"
  log "To check voice agent logs: journalctl -u $VOICE_AGENT_UNIT -f"
}

main "$@"


