#!/usr/bin/env bash
# Create/update root .env with production URLs and ports (secrets stay as you set them).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXAMPLE="${ROOT}/deploy.env.example"
ENV_FILE="${ROOT}/.env"

if [[ ! -f "$EXAMPLE" ]]; then
  echo "Missing ${EXAMPLE}" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$EXAMPLE" "$ENV_FILE"
  echo "Created ${ENV_FILE} from deploy.env.example"
fi

set_var() {
  local key="$1"
  local value="$2"
  local tmp
  tmp="$(mktemp)"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    awk -v k="$key" -v v="$value" '
      BEGIN { done = 0 }
      $0 ~ "^" k "=" {
        print k "=" v
        done = 1
        next
      }
      { print }
      END { if (!done) print k "=" v }
    ' "$ENV_FILE" >"$tmp"
  else
    cp "$ENV_FILE" "$tmp"
    printf '%s=%s\n' "$key" "$value" >>"$tmp"
  fi
  mv "$tmp" "$ENV_FILE"
}

# Copy API keys from backend/.env when present (local dev → deploy)
if [[ -f "${ROOT}/backend/.env" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT}/backend/.env"
  [[ -n "${GROQ_API_KEY:-}" ]] && set_var "GROQ_API_KEY" "$GROQ_API_KEY"
  [[ -n "${SARVAM_API_KEY:-}" ]] && set_var "SARVAM_API_KEY" "$SARVAM_API_KEY"
fi

# shellcheck disable=SC1090
source "$ENV_FILE" 2>/dev/null || true

FRONTEND_DOMAIN="${FRONTEND_DOMAIN:-voice.aavishailab.com}"
BACKEND_DOMAIN="${BACKEND_DOMAIN:-api.voice.aavishailab.com}"
BACKEND_PORT="${BACKEND_PORT:-6120}"
NGINX_CONF_DIR="${NGINX_CONF_DIR:-conf.d.http}"

set_var "FRONTEND_DOMAIN" "$FRONTEND_DOMAIN"
set_var "BACKEND_DOMAIN" "$BACKEND_DOMAIN"
set_var "BACKEND_PORT" "$BACKEND_PORT"
set_var "CORS_ORIGINS" "https://${FRONTEND_DOMAIN}"
set_var "NEXT_PUBLIC_API_URL" "https://${BACKEND_DOMAIN}"
set_var "NEXT_PUBLIC_WS_URL" "wss://${BACKEND_DOMAIN}/ws/voice"
set_var "NGINX_CONF_DIR" "$NGINX_CONF_DIR"

echo "Updated ${ENV_FILE}:"
echo "  FRONTEND_DOMAIN=${FRONTEND_DOMAIN}"
echo "  BACKEND_DOMAIN=${BACKEND_DOMAIN}"
echo "  BACKEND_PORT=${BACKEND_PORT}"
echo "  CORS_ORIGINS=https://${FRONTEND_DOMAIN}"
echo "  NEXT_PUBLIC_API_URL=https://${BACKEND_DOMAIN}"
echo "  NEXT_PUBLIC_WS_URL=wss://${BACKEND_DOMAIN}/ws/voice"
echo "  NGINX_CONF_DIR=${NGINX_CONF_DIR}"

if [[ -z "${GROQ_API_KEY:-}" || -z "${SARVAM_API_KEY:-}" ]]; then
  echo ""
  echo "Add GROQ_API_KEY and SARVAM_API_KEY to ${ENV_FILE} before deploying."
fi

if [[ -z "${CERTBOT_EMAIL:-}" ]]; then
  echo "Set CERTBOT_EMAIL in ${ENV_FILE} for Let's Encrypt."
fi
