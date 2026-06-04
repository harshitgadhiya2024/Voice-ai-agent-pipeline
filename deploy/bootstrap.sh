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

if ! "${COMPOSE[@]}" up -d backend; then
  echo "Backend failed to start. Logs:" >&2
  "${COMPOSE[@]}" logs --tail=80 backend >&2 || true
  exit 1
fi

echo "==> Waiting for backend health (up to 3 min)..."
healthy=0
for _ in $(seq 1 90); do
  if "${COMPOSE[@]}" exec -T backend curl -fsS "http://127.0.0.1:6120/health" &>/dev/null; then
    healthy=1
    break
  fi
  if ! "${COMPOSE[@]}" ps backend 2>/dev/null | grep -qE 'running|Up'; then
    echo "Backend container stopped. Logs:" >&2
    "${COMPOSE[@]}" logs --tail=100 backend >&2 || true
    exit 1
  fi
  sleep 2
done
if [[ "$healthy" -ne 1 ]]; then
  echo "Backend did not become healthy. Logs:" >&2
  "${COMPOSE[@]}" logs --tail=100 backend >&2 || true
  exit 1
fi

echo "==> Starting frontend + nginx..."
"${COMPOSE[@]}" up -d frontend nginx

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
