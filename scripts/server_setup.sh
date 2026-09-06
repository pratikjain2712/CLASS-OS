#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ClassOS — One-command server setup for Ubuntu 22.04 / 24.04 EC2
# Run as: bash server_setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

REPO_URL="https://github.com/pratikjain2712/CLASS-OS.git"
APP_DIR="$HOME/CLASS-OS"
BRANCH="claude/ai-assessment-coaching-platform-0j12i5"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── 0. Collect config ──────────────────────────────────────────────────────
echo ""
echo "=========================================="
echo "  ClassOS — AWS Deployment Setup"
echo "=========================================="
echo ""

read -rp "Your domain name (e.g. app.classos.io): " DOMAIN
[[ -z "$DOMAIN" ]] && error "Domain is required."

read -rp "Your email (for SSL certificate): " SSL_EMAIL
[[ -z "$SSL_EMAIL" ]] && error "Email is required."

read -rsp "Database password (choose a strong password): " DB_PASSWORD; echo
[[ -z "$DB_PASSWORD" ]] && error "Database password is required."

read -rsp "JWT secret key (leave blank to auto-generate): " SECRET_KEY; echo
[[ -z "$SECRET_KEY" ]] && SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

read -rsp "Anthropic API key (sk-ant-...): " ANTHROPIC_KEY; echo

read -rp "AWS S3 bucket name for file storage (leave blank to skip): " S3_BUCKET
if [[ -n "$S3_BUCKET" ]]; then
  read -rp "AWS region (e.g. ap-south-1): " AWS_REGION
  read -rsp "AWS access key ID: " AWS_ACCESS_KEY; echo
  read -rsp "AWS secret access key: " AWS_SECRET_KEY; echo
fi

echo ""
info "Starting setup for $DOMAIN..."
echo ""

# ── 1. System packages ─────────────────────────────────────────────────────
info "Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq
sudo apt-get install -y -qq \
  git curl wget unzip \
  nginx certbot python3-certbot-nginx \
  build-essential python3-pip

# awscli v2 works on both 22.04 and 24.04 via pip
pip3 install --quiet awscli 2>/dev/null || true

# ── 2. Docker ──────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  info "Installing Docker..."
  curl -fsSL https://get.docker.com | sudo bash
  sudo usermod -aG docker "$USER"
  info "Docker installed. You may need to log out and back in if docker commands fail."
else
  info "Docker already installed."
fi

if ! command -v docker &>/dev/null || ! docker compose version &>/dev/null; then
  info "Installing Docker Compose plugin..."
  sudo apt-get install -y -qq docker-compose-plugin
fi

# Make sure we can run docker without sudo in this session
if ! docker ps &>/dev/null; then
  sudo chmod 666 /var/run/docker.sock
fi

# ── 3. Clone repo ──────────────────────────────────────────────────────────
if [[ -d "$APP_DIR" ]]; then
  info "Repo already exists — pulling latest..."
  cd "$APP_DIR"
  git fetch origin
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
else
  info "Cloning repository..."
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

# ── 4. Write .env ──────────────────────────────────────────────────────────
info "Writing backend .env..."
cat > "$APP_DIR/backend/.env" << EOF
DATABASE_URL=postgresql+asyncpg://classos:${DB_PASSWORD}@db:5432/classos
SECRET_KEY=${SECRET_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
REDIS_URL=redis://redis:6379/0
EOF

if [[ -n "$S3_BUCKET" ]]; then
cat >> "$APP_DIR/backend/.env" << EOF
R2_BUCKET_NAME=${S3_BUCKET}
AWS_DEFAULT_REGION=${AWS_REGION}
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_KEY}
EOF
fi

# Write DB password for docker-compose.prod.yml
cat > "$APP_DIR/.env" << EOF
DB_USER=classos
DB_PASSWORD=${DB_PASSWORD}
EOF

# ── 5. Build frontend ──────────────────────────────────────────────────────
info "Building React frontend..."
if ! command -v node &>/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
cd "$APP_DIR/frontend"
npm install --silent
npm run build
cd "$APP_DIR"

# ── 6. Start Docker services ───────────────────────────────────────────────
info "Starting Docker services (DB, Redis, API, Celery)..."
docker compose -f docker-compose.prod.yml --env-file .env up -d --build

info "Waiting for database to be ready..."
sleep 15

# ── 7. Seed demo data ─────────────────────────────────────────────────────
info "Seeding demo data..."
docker compose -f docker-compose.prod.yml exec -T api \
  python /app/scripts/seed_demo.py || warn "Seed may have already run — continuing."

# ── 8. Nginx ───────────────────────────────────────────────────────────────
info "Configuring Nginx..."
sudo cp "$APP_DIR/nginx/classos.conf" /etc/nginx/sites-available/classos
sudo sed -i "s/__DOMAIN__/${DOMAIN}/g" /etc/nginx/sites-available/classos

# Temp HTTP-only config for certbot to verify domain
sudo bash -c "cat > /etc/nginx/sites-available/classos_temp << 'TEMP'
server {
    listen 80;
    server_name ${DOMAIN};
    root /var/www/html;
    location /.well-known/acme-challenge/ { allow all; }
    location / { return 200 'ClassOS setup in progress'; }
}
TEMP"

sudo ln -sf /etc/nginx/sites-available/classos_temp /etc/nginx/sites-enabled/classos
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# ── 9. SSL certificate ─────────────────────────────────────────────────────
info "Obtaining SSL certificate for $DOMAIN..."
if sudo certbot certonly --nginx \
  --non-interactive \
  --agree-tos \
  --email "$SSL_EMAIL" \
  --domains "$DOMAIN"; then
  # SSL succeeded — use the full HTTPS config
  sudo cp "$APP_DIR/nginx/classos.conf" /etc/nginx/sites-available/classos
  sudo sed -i "s/__DOMAIN__/${DOMAIN}/g" /etc/nginx/sites-available/classos
  sudo ln -sf /etc/nginx/sites-available/classos /etc/nginx/sites-enabled/classos
else
  warn "SSL skipped (bare IP or certbot error) — running HTTP only."
  # Fall back to plain HTTP config
  sudo cp "$APP_DIR/nginx/classos_http.conf" /etc/nginx/sites-available/classos
  sudo ln -sf /etc/nginx/sites-available/classos /etc/nginx/sites-enabled/classos
fi
sudo rm -f /etc/nginx/sites-available/classos_temp
sudo nginx -t && sudo systemctl reload nginx

# ── 10. Backup cron ───────────────────────────────────────────────────────
info "Setting up daily database backup..."
BACKUP_DIR="$HOME/backups"
mkdir -p "$BACKUP_DIR"

cat > "$HOME/scripts/backup.sh" << 'BACKUP'
#!/usr/bin/env bash
set -e
BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/classos_${DATE}.sql.gz"
mkdir -p "$BACKUP_DIR"

docker compose -f "$HOME/CLASS-OS/docker-compose.prod.yml" exec -T db \
  pg_dump -U classos classos | gzip > "$FILE"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "[$(date)] Backup completed: $FILE"
BACKUP
chmod +x "$HOME/scripts/backup.sh"

# Add cron job at 2am IST (8:30 PM UTC)
(crontab -l 2>/dev/null; echo "30 20 * * * $HOME/scripts/backup.sh >> $HOME/backups/backup.log 2>&1") | crontab -

# ── 11. Auto-renew SSL ────────────────────────────────────────────────────
info "SSL auto-renewal is handled by certbot systemd timer (already active)."

# ── 12. Save deployment info ──────────────────────────────────────────────
cat > "$APP_DIR/DEPLOY_INFO.txt" << INFO
ClassOS Deployment
==================
Domain:   https://${DOMAIN}
API docs: https://${DOMAIN}/docs
Health:   https://${DOMAIN}/health

Deployed: $(date)
Branch:   ${BRANCH}

Demo login:
  Teacher: priya@arihant.edu / teacher123
  Admin:   admin@classos.io  / admin123

Useful commands:
  View logs:      docker compose -f ~/CLASS-OS/docker-compose.prod.yml logs -f api
  Restart API:    docker compose -f ~/CLASS-OS/docker-compose.prod.yml restart api
  Update app:     bash ~/CLASS-OS/scripts/update.sh
  Manual backup:  bash ~/scripts/backup.sh
INFO

echo ""
echo "=========================================="
echo -e "${GREEN}  ClassOS deployed successfully!${NC}"
echo "=========================================="
cat "$APP_DIR/DEPLOY_INFO.txt"
echo ""
