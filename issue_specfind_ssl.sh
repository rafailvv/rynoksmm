#!/bin/sh

set -eu

COMPOSE_FILE="docker-compose.nginx.yml"
WEBROOT_HOST="/var/www/letsencrypt"
BOOTSTRAP_DIR="/etc/nginx/bootstrap"
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
  $0 your@email.com

Environment variables:
  LETSENCRYPT_EMAIL  Email for Let's Encrypt account
  STAGING=1          Use Let's Encrypt staging endpoint
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

EMAIL="${1:-${LETSENCRYPT_EMAIL:-}}"

if [ -z "${EMAIL}" ]; then
    echo "Email is required"
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE_BIN="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_BIN="docker-compose"
else
    echo "docker compose not found"
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

#
# bootstrap certificate
#
mkdir -p "${BOOTSTRAP_DIR}"

if [ ! -f "${BOOTSTRAP_DIR}/fullchain.pem" ] || [ ! -f "${BOOTSTRAP_DIR}/privkey.pem" ]; then
    echo "Creating bootstrap certificate"

    openssl req \
        -x509 \
        -nodes \
        -newkey rsa:2048 \
        -days 1 \
        -keyout "${BOOTSTRAP_DIR}/privkey.pem" \
        -out "${BOOTSTRAP_DIR}/fullchain.pem" \
        -subj "/CN=bootstrap"
fi

echo "Starting nginx"
run_compose up -d nginx

sleep 5

echo "Checking nginx"

if ! run_compose exec nginx nginx -t; then
    echo "nginx config invalid"
    exit 1
fi

STAGING_FLAG=""

if [ "${STAGING:-0}" = "1" ]; then
    STAGING_FLAG="--staging"
fi

echo "Requesting certificates"

for domain in ${DOMAINS}; do
    echo ">>> ${domain}"

    run_compose run --rm --entrypoint certbot certbot \
        certonly \
        --webroot \
        -w /var/www/letsencrypt \
        -d "${domain}" \
        --cert-name "${domain}" \
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

echo "Done"