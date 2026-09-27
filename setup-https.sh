#!/bin/bash
# Sets up local HTTPS: starts Docker stack with Caddy and trusts the CA on macOS.
set -e

echo "=== AI Opportunity Platform — HTTPS Setup ==="
echo ""

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Install Docker Desktop: https://docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo "Docker daemon is not running. Start Docker Desktop first."
    exit 1
fi

echo "[1/3] Building + starting containers…"
docker compose up -d --build postgres backend frontend caddy

echo ""
echo "[2/3] Waiting for Caddy to generate its local CA…"
sleep 5

echo ""
echo "[3/3] Extracting Caddy CA for trust…"
docker compose exec -T caddy cat /data/caddy/pki/authorities/local/root.crt > /tmp/caddy-root.crt

echo ""
echo "=========================================================="
echo " HTTPS is now available at:"
echo "   Frontend + API:  https://localhost:8443"
echo "   Backend direct:  https://localhost:8444/docs"
echo ""
echo " To trust the certificate in your browser, run:"
echo "   sudo security add-trusted-cert -d -r trustRoot \\"
echo "     -k /Library/Keychains/System.keychain /tmp/caddy-root.crt"
echo ""
echo " Then open: https://localhost:8443"
echo "=========================================================="
