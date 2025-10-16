#!/usr/bin/env bash

set -euo pipefail

# ==============================================================================
# Integro Agents - Local helper to deploy to remote droplet
# - Copies project files to remote (rsync)
# - Copies local .env if present
# - Uploads remote deploy script and runs it with proper env
# - Deploys backend, frontend, and voice agent services
# 
# Usage:
#   scripts/deploy_to_droplet.sh \
#     --host root@164.92.90.150 \
#     --domain xarov.com \
#     [--app-dir /opt/integro-agents]
#
# Required .env variables for voice agent:
#   LIVEKIT_URL=wss://your-project.livekit.cloud
#   LIVEKIT_API_KEY=your_livekit_api_key
#   LIVEKIT_API_SECRET=your_livekit_api_secret
#   ASSEMBLYAI_API_KEY=your_assemblyai_api_key
#   CARTESIA_API_KEY=your_cartesia_api_key
# ==============================================================================

REMOTE_HOST=""
DOMAIN="xarov.com"
APP_DIR="/opt/integro-agents"
# Basic auth defaults (can be overridden via environment)
BASIC_AUTH_USER="${BASIC_AUTH_USER:-integro}"
BASIC_AUTH_PASSWORD="${BASIC_AUTH_PASSWORD:-gointegro}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      REMOTE_HOST="$2"; shift 2 ;;
    --domain)
      DOMAIN="$2"; shift 2 ;;
    --app-dir)
      APP_DIR="$2"; shift 2 ;;
    *)
      echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$REMOTE_HOST" ]]; then
  echo "--host is required (e.g., root@164.92.90.150)" >&2
  exit 1
fi

log() { echo "[local-deploy] $*"; }

# Ensure remote path
ssh -o StrictHostKeyChecking=no "$REMOTE_HOST" "mkdir -p '$APP_DIR' '$APP_DIR/scripts'"

# Rsync project files (exclude heavy/irrelevant dirs)
log "Syncing project files to $REMOTE_HOST:$APP_DIR"
rsync -az --delete \
  --exclude='.git/' \
  --exclude='node_modules/' \
  --exclude='frontend/node_modules/' \
  --exclude='frontend/.next/' \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='data/' \
  --exclude='qdrant/' \
  --exclude='build/' \
  --exclude='*.pyc' \
  ./ "$REMOTE_HOST":"$APP_DIR/"

# Copy .env if present (overwrite to ensure updates are deployed)
if [[ -f .env ]]; then
  log "Uploading local .env (overwriting remote)"
  scp -o StrictHostKeyChecking=no .env "$REMOTE_HOST":"$APP_DIR/.env"
  ssh -o StrictHostKeyChecking=no "$REMOTE_HOST" "chmod 600 '$APP_DIR/.env'"
fi

# Upload remote deploy script
log "Uploading remote deploy script"
scp -o StrictHostKeyChecking=no scripts/deploy_droplet.sh "$REMOTE_HOST":"$APP_DIR/scripts/deploy_droplet.sh"
ssh -o StrictHostKeyChecking=no "$REMOTE_HOST" "chmod +x '$APP_DIR/scripts/deploy_droplet.sh'"

# Run remote deploy with env
log "Running remote deployment"
ssh -o StrictHostKeyChecking=no "$REMOTE_HOST" \
  "DOMAIN='$DOMAIN' APP_DIR='$APP_DIR' BASIC_AUTH_USER='$BASIC_AUTH_USER' BASIC_AUTH_PASSWORD='$BASIC_AUTH_PASSWORD' bash '$APP_DIR/scripts/deploy_droplet.sh'"

log "Deployment triggered. Verify at: https://$DOMAIN"
log "Services deployed: backend, frontend, voice-agent"
log "To check voice agent logs: ssh $REMOTE_HOST 'journalctl -u integro-voice-agent.service -f'"


