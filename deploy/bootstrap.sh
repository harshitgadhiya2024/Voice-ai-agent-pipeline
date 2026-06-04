#!/usr/bin/env bash
# First-time production deploy: env → build → HTTP → SSL certs → HTTPS + renew loop.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x deploy/setup-env.sh
./deploy/setup-env.sh

# shellcheck disable=SC1091
set -a
source .env
set +a

for var in GROQ_API_KEY SARVAM_API_KEY CERTBOT_EMAIL; do
  if [[ -z "${!var:-}" ]]; then
    echo "Missing ${var} in .env — edit .env and re-run ./deploy/bootstrap.sh" >&2
    exit 1
  fi
done

COMPOSE=(docker compose)
if ! docker compose version &>/dev/null; then
  COMPOSE=(docker-compose)
fi

echo "==> Building images..."
"${COMPOSE[@]}" build

echo "==> Starting stack (HTTP only, port 80)..."
set_var_nginx_http() {
  local tmp
  tmp="$(mktemp)"
  awk '
    BEGIN { done = 0 }
    /^NGINX_CONF_DIR=/ { print "NGINX_CONF_DIR=conf.d.http"; done = 1; next }
    { print }
    END { if (!done) print "NGINX_CONF_DIR=conf.d.http" }
  ' .env >"$tmp" && mv "$tmp" .env
}
set_var_nginx_http
export NGINX_CONF_DIR=conf.d.http

"${COMPOSE[@]}" up -d backend frontend nginx

echo "==> Waiting for backend health..."
for _ in $(seq 1 60); do
  if "${COMPOSE[@]}" exec -T backend curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" &>/dev/null; then
    break
  fi
  sleep 2
done

echo "==> Requesting Let's Encrypt certificate..."
"${COMPOSE[@]}" run --rm certbot-init

echo "==> Enabling HTTPS (nginx SSL config)..."
tmp="$(mktemp)"
awk '
  BEGIN { done = 0 }
  /^NGINX_CONF_DIR=/ { print "NGINX_CONF_DIR=conf.d.ssl"; done = 1; next }
  { print }
  END { if (!done) print "NGINX_CONF_DIR=conf.d.ssl" }
' .env >"$tmp" && mv "$tmp" .env
export NGINX_CONF_DIR=conf.d.ssl

"${COMPOSE[@]}" up -d nginx certbot

echo ""
echo "Deploy complete."
echo "  Frontend: https://${FRONTEND_DOMAIN}"
echo "  Backend:  https://${BACKEND_DOMAIN} (internal port ${BACKEND_PORT})"
echo ""
echo "Renewal: certbot container runs every 12h. Reload nginx after renew:"
echo "  ${COMPOSE[*]} exec nginx nginx -s reload"
