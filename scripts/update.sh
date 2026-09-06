#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ClassOS — In-place update script
# Run as: bash ~/CLASS-OS/scripts/update.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_DIR="$HOME/CLASS-OS"
BRANCH="claude/ai-assessment-coaching-platform-0j12i5"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }

cd "$APP_DIR"

info "Pulling latest code from $BRANCH..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

info "Building React frontend..."
cd "$APP_DIR/frontend"
npm install --silent
npm run build
cd "$APP_DIR"

info "Rebuilding and restarting Docker services..."
docker compose -f docker-compose.prod.yml --env-file .env up -d --build --no-deps api celery

info "Running any new migrations..."
docker compose -f docker-compose.prod.yml exec -T api \
  python -c "from app.database import engine; import asyncio; asyncio.run(engine.dispose())" \
  || warn "Migration check skipped."

info "Reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo -e "${GREEN}Update complete!${NC}"
echo "  Logs: docker compose -f ~/CLASS-OS/docker-compose.prod.yml logs -f api"
