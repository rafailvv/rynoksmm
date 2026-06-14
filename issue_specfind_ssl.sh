#!/bin/sh

set -eu

COMPOSE_FILE="docker-compose.nginx.yml"
WEBROOT_HOST="/var/www/letsencrypt"
RSA_KEY_SIZE="4096"

DOMAINS="
smm.specfind.ru
massage.specfind.ru
event.specfind.ru
specfind.ru
s3.specfind.ru
console.s3.specfind.ru
grafana.smm.specfind.ru
grafana.massage.specfind.ru
grafana.event.specfind.ru
"

usage() {
    cat <<EOF
Usage:
  $0 v.k0korev@yandex.com

Environment variables:
  LETSENCRYPT_EMAIL  Email for Let's Encrypt account
  STAGING=1          Use Let's Encrypt staging endpoint

This script expects:
  - docker / docker-compose to be available
  - nginx from ${COMPOSE_FILE} to already be running
  - DNS for all domains to point to this server
  - port 80 to be reachable from the internet
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

EMAIL="${1:-${LETSENCRYPT_EMAIL:-}}"
if [ -z "${EMAIL}" ]; then
    echo "Error: email is required."
    usage
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE_BIN="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_BIN="docker-compose"
else
    echo "Error: neither 'docker compose' nor 'docker-compose' was found."
    exit 1
fi

run_compose() {
    if [ "${COMPOSE_BIN}" = "docker compose" ]; then
        docker compose -f "${COMPOSE_FILE}" "$@"
    else
        docker-compose -f "${COMPOSE_FILE}" "$@"
    fi
}

mkdir -p "${WEBROOT_HOST}/.well-known/acme-challenge"

if ! run_compose ps --services --status running | grep -qx "nginx"; then
    echo "Error: nginx service from ${COMPOSE_FILE} is not running."
    echo "Start it first, for example:"
    echo "  docker-compose -f ${COMPOSE_FILE} up -d nginx"
    exit 1
fi

STAGING_FLAG=""
if [ "${STAGING:-0}" = "1" ]; then
    STAGING_FLAG="--staging"
fi

echo "Issuing certificates via webroot ${WEBROOT_HOST}"
for domain in ${DOMAINS}; do
    echo ">>> ${domain}"
    run_compose run --rm --entrypoint certbot certbot \
        certonly \
        --webroot \
        -w /var/www/letsencrypt \
        -d "${domain}" \
        --non-interactive \
        --agree-tos \
        --email "${EMAIL}" \
        --rsa-key-size "${RSA_KEY_SIZE}" \
        --keep-until-expiring \
        ${STAGING_FLAG}
done

echo "Validating nginx config"
run_compose exec nginx nginx -t

echo "Reloading nginx"
run_compose exec nginx nginx -s reload

echo "Done."
