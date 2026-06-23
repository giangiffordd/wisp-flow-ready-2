#!/usr/bin/env bash
# Timestamped backup of scans.db and saved_images/. Cron-friendly: no
# interactive prompts, logs to stdout, exits non-zero only on real failure.
#
# Usage: scripts/backup.sh
# Cron:  0 * * * * /opt/wisp-flow-ai/scripts/backup.sh >> /opt/wisp-flow-ai/backups/backup.log 2>&1
set -euo pipefail

APP_DIR="${WISP_APP_DIR:-/opt/wisp-flow-ai}"
BACKUP_DIR="${WISP_BACKUP_DIR:-$APP_DIR/backups}"
DB_PATH="$APP_DIR/scans.db"
IMAGES_DIR="$APP_DIR/saved_images"
KEEP=7

mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

if [ -f "$DB_PATH" ]; then
    DB_BACKUP="$BACKUP_DIR/scans_${TIMESTAMP}.db"
    if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 "$DB_PATH" ".backup '$DB_BACKUP'"
    else
        cp "$DB_PATH" "$DB_BACKUP"
    fi
    echo "[backup] scans.db -> $DB_BACKUP"
else
    echo "[backup] WARNING: $DB_PATH not found, skipping DB backup" >&2
fi

if [ -d "$IMAGES_DIR" ] && [ -n "$(ls -A "$IMAGES_DIR" 2>/dev/null)" ]; then
    IMAGES_BACKUP="$BACKUP_DIR/saved_images_${TIMESTAMP}.tar.gz"
    tar -czf "$IMAGES_BACKUP" -C "$APP_DIR" saved_images
    echo "[backup] saved_images/ -> $IMAGES_BACKUP"
else
    echo "[backup] saved_images/ empty or missing, skipping image backup"
fi

# Prune: keep only the most recent $KEEP of each artifact type.
cd "$BACKUP_DIR"
ls -1t scans_*.db 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f --
ls -1t saved_images_*.tar.gz 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f --

DB_COUNT=$(ls -1 scans_*.db 2>/dev/null | wc -l)
IMG_COUNT=$(ls -1 saved_images_*.tar.gz 2>/dev/null | wc -l)
echo "[backup] done — retaining $DB_COUNT DB backup(s), $IMG_COUNT image archive(s) in $BACKUP_DIR"
