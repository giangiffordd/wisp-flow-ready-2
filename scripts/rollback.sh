#!/usr/bin/env bash
# Roll back the running deployment to a prior git commit and restore the
# most recent scans.db backup (see backup.sh). Stops the running uvicorn
# process, checks out the target commit, restores the DB, then restarts.
#
# Usage: scripts/rollback.sh [git-ref] [--yes]
#   [git-ref]  commit hash, tag, or relative ref (default: HEAD~1, i.e. the
#              commit before whatever is currently deployed)
#   --yes      skip the confirmation prompt (for non-interactive use)
set -euo pipefail

APP_DIR="${WISP_APP_DIR:-/opt/wisp-flow-ai}"
BACKUP_DIR="${WISP_BACKUP_DIR:-$APP_DIR/backups}"
LOG_FILE="$APP_DIR/server.log"
PORT="${WISP_PORT:-8000}"

TARGET="${1:-HEAD~1}"
AUTO_YES=false
[ "${2:-}" = "--yes" ] && AUTO_YES=true

cd "$APP_DIR"

if ! RESOLVED="$(git rev-parse --short "$TARGET" 2>/dev/null)"; then
    echo "Error: '$TARGET' is not a valid git ref in $APP_DIR" >&2
    exit 1
fi
CURRENT="$(git rev-parse --short HEAD)"

echo "Current commit:  $CURRENT"
echo "Rollback target: $RESOLVED ($TARGET)"

if [ "$AUTO_YES" != true ]; then
    read -rp "Stop the server and roll back? [y/N] " confirm
    case "$confirm" in
        [Yy]*) ;;
        *) echo "Aborted."; exit 1 ;;
    esac
fi

echo "[rollback] stopping server on port $PORT..."
if command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" 2>/dev/null && echo "[rollback] server stopped." || echo "[rollback] no server was listening on $PORT."
else
    pkill -f "python.*main\.py" 2>/dev/null || true
fi
sleep 1
if pgrep -f "python.*main\.py" >/dev/null 2>&1; then
    echo "[rollback] process still alive, sending SIGKILL..."
    pkill -9 -f "python.*main\.py" 2>/dev/null || true
    sleep 1
fi

echo "[rollback] checking out $RESOLVED..."
git checkout "$TARGET"

LATEST_DB_BACKUP="$(ls -1t "$BACKUP_DIR"/scans_*.db 2>/dev/null | head -n 1 || true)"
if [ -n "$LATEST_DB_BACKUP" ]; then
    echo "[rollback] restoring database from $LATEST_DB_BACKUP"
    cp "$LATEST_DB_BACKUP" "$APP_DIR/scans.db"
else
    echo "[rollback] WARNING: no DB backup found in $BACKUP_DIR — leaving scans.db as-is" >&2
fi

echo "[rollback] restarting server..."
cd "$APP_DIR"
nohup venv/bin/python main.py >> "$LOG_FILE" 2>&1 &
disown
sleep 2

if pgrep -f "python.*main\.py" >/dev/null 2>&1; then
    echo "[rollback] server restarted (pid $(pgrep -f "python.*main\.py" | head -n1)). Logs: $LOG_FILE"
else
    echo "[rollback] WARNING: server process not detected after restart — check $LOG_FILE" >&2
    exit 1
fi

echo "[rollback] complete — now running commit $RESOLVED."
