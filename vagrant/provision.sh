#!/usr/bin/env bash
# Provision a prod-faithful Tin dev environment on Ubuntu 24.04.
# Runs Tin natively (not dockerized) so firejail + bubblewrap actually engage.
set -euo pipefail

APP_SRC=/vagrant          # repo mounted here (vboxsf)
# Under /home (NOT /opt): grader.profile marks /opt read-only, which blocks the
# sandbox from writing grader files / submissions into media. Production runs
# Tin under /home/tin for the same reason.
APP_DIR=/home/vagrant/tin # native copy we actually run from
APP_USER=vagrant
UV="/home/${APP_USER}/.local/bin/uv"

echo "==> [1/7] Installing system packages (firejail, bubblewrap, JDK 17, redis, ...)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
# JDK 17 specifically: grader.profile's private-etc whitelists java-17-openjdk
# (not 21), so 17 is what works under the firejail sandbox.
apt-get install -y --no-install-recommends \
  firejail bubblewrap openjdk-17-jdk-headless \
  redis-server git curl ca-certificates rsync build-essential

echo "==> [2/7] Enabling redis + allowing unprivileged user namespaces (bubblewrap)"
systemctl enable --now redis-server
# Ubuntu 24.04 restricts unprivileged user namespaces, which bubblewrap needs to
# sandbox submissions; without this bwrap fails with "setting up uid map:
# Permission denied". (Fine on a throwaway dev VM.)
echo "kernel.apparmor_restrict_unprivileged_userns = 0" > /etc/sysctl.d/99-tin-userns.conf
sysctl --system >/dev/null 2>&1 || true

echo "==> [3/7] Copying app source to native fs (${APP_DIR})"
mkdir -p "$APP_DIR"
rsync -a --delete \
  --exclude '.git' --exclude '.vagrant' --exclude 'media' \
  --exclude '.venv' --exclude 'node_modules' --exclude 'db.sqlite3' \
  --exclude 'serve' --exclude 'logs' --exclude '__pycache__' \
  "$APP_SRC"/ "$APP_DIR"/
# BASE_DIR is /opt/tin/tin; it needs logs/ and media/ to exist.
mkdir -p "$APP_DIR/tin/logs" "$APP_DIR/tin/media"
chown -R "${APP_USER}:${APP_USER}" "$APP_DIR"

echo "==> [4/7] Installing uv for ${APP_USER}"
sudo -u "$APP_USER" bash -lc 'command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh'

echo "==> [5/7] uv sync (downloads Python 3.14 + dependencies)"
sudo -u "$APP_USER" bash -lc "cd '$APP_DIR' && '$UV' sync"

echo "==> [6/7] Migrate DB + create debug users (admin/teacher/student, pw 'jasongrace')"
sudo -u "$APP_USER" bash -lc "cd '$APP_DIR' && '$UV' run python manage.py migrate --noinput"
sudo -u "$APP_USER" bash -lc "cd '$APP_DIR' && '$UV' run python manage.py create_debug_users --noinput"

echo "==> [7/7] Installing systemd services (tin-celery, tin-web)"
cat >/etc/systemd/system/tin-celery.service <<UNIT
[Unit]
Description=Tin Celery worker
After=redis-server.service
Requires=redis-server.service

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${UV} run celery -A tin worker --loglevel=info
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

cat >/etc/systemd/system/tin-web.service <<UNIT
[Unit]
Description=Tin Django dev server
After=network.target redis-server.service

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${UV} run python manage.py runserver 0.0.0.0:8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable tin-celery.service tin-web.service
systemctl restart tin-celery.service tin-web.service

echo
echo "======================================================================"
echo " Tin is running natively with REAL firejail + bubblewrap."
echo "   URL:        http://localhost:8000   (login at /password-login/)"
echo "   users:      admin / teacher / student   (password: jasongrace)"
echo "   app dir:    ${APP_DIR}   (BASE_DIR=${APP_DIR}/tin)"
echo "   logs:       journalctl -u tin-web -u tin-celery -f"
echo " Re-sync code after host edits:  vagrant provision"
echo "======================================================================"
