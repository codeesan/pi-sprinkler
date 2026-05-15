#!/bin/bash
# Sprinkler controller install script
# Run with: sudo bash deploy/install.sh
# Must be run from the project root directory.

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve paths — works whether the Pi user is 'pi', or anything else
# ---------------------------------------------------------------------------
DEPLOY_USER="${SUDO_USER:-$(whoami)}"
DEPLOY_HOME="$(eval echo ~"$DEPLOY_USER")"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/sprinklers_venv"
API_DIR="$PROJECT_DIR/api"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "Installing sprinkler controller"
echo "  Project : $PROJECT_DIR"
echo "  User    : $DEPLOY_USER"
echo ""

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
echo ">>> Installing system packages..."
apt-get update -q
apt-get install -y nginx python3 python3-venv python3-pip nodejs npm

# ---------------------------------------------------------------------------
# 2. Python virtual environment + dependencies
# ---------------------------------------------------------------------------
echo ">>> Setting up Python virtualenv..."
sudo -u "$DEPLOY_USER" python3 -m venv "$VENV_DIR"
sudo -u "$DEPLOY_USER" "$VENV_DIR/bin/pip" install --upgrade pip -q
sudo -u "$DEPLOY_USER" "$VENV_DIR/bin/pip" install -r "$API_DIR/requirements.txt" -q
echo "    Done."

# ---------------------------------------------------------------------------
# 3. Build the Vue frontend
# ---------------------------------------------------------------------------
echo ">>> Building frontend..."
cd "$FRONTEND_DIR"
sudo -u "$DEPLOY_USER" npm install --silent
sudo -u "$DEPLOY_USER" npm run build --silent
echo "    Done — dist/ ready."
cd "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# 4. systemd service for the API
# ---------------------------------------------------------------------------
echo ">>> Installing sprinkler-api systemd service..."
SERVICE_SRC="$PROJECT_DIR/deploy/sprinkler-api.service"
SERVICE_DST="/etc/systemd/system/sprinkler-api.service"

cp "$SERVICE_SRC" "$SERVICE_DST"
# Substitute actual user and home directory into the service file
sed -i \
    "s|User=pi|User=$DEPLOY_USER|g; \
     s|/home/pi|$DEPLOY_HOME|g" \
    "$SERVICE_DST"

systemctl daemon-reload
systemctl enable sprinkler-api
systemctl restart sprinkler-api
echo "    sprinkler-api service enabled and started."

# ---------------------------------------------------------------------------
# 5. nginx config for the frontend
# ---------------------------------------------------------------------------
echo ">>> Configuring nginx..."
NGINX_SRC="$PROJECT_DIR/deploy/nginx-sprinkler.conf"
NGINX_DST="/etc/nginx/sites-available/sprinkler"

cp "$NGINX_SRC" "$NGINX_DST"
sed -i "s|/home/pi|$DEPLOY_HOME|g" "$NGINX_DST"

ln -sf "$NGINX_DST" /etc/nginx/sites-enabled/sprinkler
# Remove the default nginx placeholder site if present
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable nginx
systemctl restart nginx
echo "    nginx configured and restarted."

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "================================================"
echo "  Sprinkler controller is running!"
echo ""
echo "  Frontend : http://$IP"
echo "  API      : http://$IP:8000"
echo "  API docs : http://$IP:8000/docs"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status sprinkler-api"
echo "    sudo journalctl -u sprinkler-api -f"
echo "    sudo systemctl restart sprinkler-api"
echo "================================================"
