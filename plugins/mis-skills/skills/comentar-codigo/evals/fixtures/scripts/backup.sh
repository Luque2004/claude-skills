#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-$HOME/proyectos}"
DEST="${2:-/mnt/backup}"
KEEP=7
STAMP=$(date +%Y%m%d-%H%M%S)
LOG="$DEST/backup.log"

mkdir -p "$DEST"

if ! mountpoint -q "$DEST" && [[ "$DEST" == /mnt/* ]]; then
  echo "[$STAMP] destino no montado: $DEST" >> "$LOG"
  exit 1
fi

EXCLUDES=()
while IFS= read -r dir; do
  EXCLUDES+=("--exclude=$dir")
done < <(find "$SRC" -type d \( -name node_modules -o -name .git -o -name venv \) -prune -print)

tar czf "$DEST/backup-$STAMP.tar.gz" "${EXCLUDES[@]}" -C "$(dirname "$SRC")" "$(basename "$SRC")"
SIZE=$(du -h "$DEST/backup-$STAMP.tar.gz" | cut -f1)
echo "[$STAMP] ok $SIZE" >> "$LOG"

ls -1t "$DEST"/backup-*.tar.gz | tail -n +$((KEEP + 1)) | while read -r old; do
  if [[ "$old" =~ backup-([0-9]{8})-[0-9]{6}\.tar\.gz$ ]]; then
    rm -f "$old"
    echo "[$STAMP] borrado ${BASH_REMATCH[1]}" >> "$LOG"
  fi
done
