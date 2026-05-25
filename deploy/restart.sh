#!/bin/bash
# Post-pull restart script for the sprinkler controller.
# Run from the project root after pulling the latest branch:
#   bash deploy/restart.sh
#
# Requires passwordless sudo for systemctl, or run as root.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/sprinklers_venv"
API_DIR="$PROJECT_DIR/api"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "=== Sprinkler restart ==="
echo "  Project : $PROJECT_DIR"
echo ""

# ---------------------------------------------------------------------------
# 1. Sync Python dependencies
# ---------------------------------------------------------------------------
echo ">>> Syncing Python dependencies..."
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -r "$API_DIR/requirements.txt"
echo "    Done."

# ---------------------------------------------------------------------------
# 2. Rebuild the Vue frontend
# ---------------------------------------------------------------------------
echo ">>> Rebuilding frontend..."
cd "$FRONTEND_DIR"
npm install --silent
npm run build --silent
cd "$PROJECT_DIR"

# Ensure nginx (www-data) can read the new dist/
DEPLOY_HOME="$(eval echo ~"$(whoami)")"
chmod o+x "$DEPLOY_HOME"
chmod -R o+rX "$FRONTEND_DIR/dist"
echo "    Done — dist/ updated."

# ---------------------------------------------------------------------------
# 3. Restart the API service
# ---------------------------------------------------------------------------
echo ">>> Restarting sprinkler-api..."
sudo systemctl restart sprinkler-api
sudo systemctl is-active --quiet sprinkler-api && echo "    Service is running." || {
    echo "    ERROR: sprinkler-api failed to start."
    sudo journalctl -u sprinkler-api -n 20 --no-pager
    exit 1
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "================================================"
echo "  Ready!"
echo "  Frontend : http://$IP"
echo "  API      : http://$IP:8000"
echo "  Logs     : sudo journalctl -u sprinkler-api -f"
echo "================================================"
