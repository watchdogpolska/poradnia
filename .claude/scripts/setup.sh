#!/usr/bin/env bash
# Setup script for Claude Code sessions.
# Ensures the development environment is ready: Docker daemon, MySQL, Python venv, migrations.
set -euo pipefail

PROJECT_DIR="/home/user/poradnia"
VENV_DIR="/opt/poradnia-venv"
PYTHON_VERSION="3.13"

cd "$PROJECT_DIR"

# ── 1. Configure and start Docker daemon ──────────────────────────────────
# Configure proxy before starting, so Docker only needs to start once
if [ -n "${HTTP_PROXY:-}" ] && [ ! -f /etc/docker/daemon.json ]; then
    echo "Configuring Docker daemon proxy..."
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json <<EOF
{
  "proxies": {
    "http-proxy": "${HTTP_PROXY}",
    "https-proxy": "${HTTPS_PROXY:-}",
    "no-proxy": "${NO_PROXY:-localhost,127.0.0.1}"
  }
}
EOF
fi

if ! docker info &>/dev/null; then
    echo "Starting Docker daemon..."
    sudo dockerd &>/var/log/dockerd.log &
    for i in $(seq 1 15); do
        docker info &>/dev/null && break
        sleep 2
    done
    if ! docker info &>/dev/null; then
        echo "ERROR: Docker daemon failed to start" >&2
        exit 1
    fi
fi

echo "Docker daemon is running."

# ── 2. Install Python via uv and create venv ───────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "ERROR: uv is not installed" >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ] || [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Installing Python ${PYTHON_VERSION} and creating venv..."
    uv python install "$PYTHON_VERSION"
    uv venv "$VENV_DIR" --python "$PYTHON_VERSION" --seed --clear
    echo "Installing Python dependencies..."
    uv pip install -r "$PROJECT_DIR/requirements/dev.txt" --python "$VENV_DIR/bin/python"
else
    # Verify correct Python version
    CURRENT_PY=$("$VENV_DIR/bin/python" --version 2>&1 | grep -oP '\d+\.\d+')
    if [ "$CURRENT_PY" != "$PYTHON_VERSION" ]; then
        echo "Recreating venv with Python ${PYTHON_VERSION}..."
        uv python install "$PYTHON_VERSION"
        uv venv "$VENV_DIR" --python "$PYTHON_VERSION" --seed --clear
        uv pip install -r "$PROJECT_DIR/requirements/dev.txt" --python "$VENV_DIR/bin/python"
    fi
fi

echo "Python venv ready at $VENV_DIR"

# ── 3. Install host-level MySQL client (needed for mysqlclient Python pkg) ─
if ! command -v mysql &>/dev/null; then
    echo "Installing MySQL client..."
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
        default-libmysqlclient-dev default-mysql-client \
        build-essential pkg-config gcc libssl-dev python3-dev \
        gettext libgettextpo-dev
fi

# ── 4. Start MySQL container ───────────────────────────────────────────────
echo "Starting MySQL container..."
docker compose up -d --remove-orphans db 2>&1 | grep -v "^time=" || true

echo "Waiting for MySQL..."
for i in $(seq 1 30); do
    if mysql -h 127.0.0.1 -P 3306 -u root -ppassword -e "SELECT 1" &>/dev/null; then
        break
    fi
    sleep 3
done

if ! mysql -h 127.0.0.1 -P 3306 -u root -ppassword -e "SELECT 1" &>/dev/null; then
    echo "ERROR: MySQL failed to start" >&2
    exit 1
fi
echo "MySQL is ready."

# ── 5. Run Django migrations ───────────────────────────────────────────────
echo "Running Django migrations..."
source "$VENV_DIR/bin/activate"
export DATABASE_URL="mysql://root:password@127.0.0.1:3306/poradnia"
export DJANGO_SETTINGS_MODULE="config.settings.local"
export GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID:-}"
export GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET:-}"
export ROSETTA_AZURE_CLIENT_SECRET="${ROSETTA_AZURE_CLIENT_SECRET:-}"
export TURNSTILE_SITE_KEY="${TURNSTILE_SITE_KEY:-}"
export TURNSTILE_SECRET_KEY="${TURNSTILE_SECRET_KEY:-}"
export MY_INTERNAL_IP="${MY_INTERNAL_IP:-}"
export NGROK_URL="${NGROK_URL:-http://localhost}"
export LETTER_RECEIVE_SECRET="dev_letter_receive_very_secret"
export LETTER_RECEIVE_WHITELISTED_ADDRESS="porady@porady.siecobywatelska.pl,porady@dev.porady.siecobywatelska.pl"
export APP_MODE="DEV"
export E2E_MFA_BYPASS_SECRET="supersecret-123"
export DJANGO_EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
export DJANGO_DEFAULT_FROM_EMAIL="poradnia_dev <noreply@dev.porady.siecobywatelska.pl>"
export DJANGO_RICH_TEXT_ENABLED="False"

python manage.py migrate --no-input 2>&1 | tail -5

echo ""
echo "=== Environment ready ==="
echo "  Python:   $("$VENV_DIR/bin/python" --version)"
echo "  MySQL:    running on 127.0.0.1:3306"
echo "  Activate: source $VENV_DIR/bin/activate"
echo "  Run tests: python manage.py test --keepdb --verbosity=2"
echo ""
