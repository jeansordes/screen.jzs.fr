#!/usr/bin/env bash
set -euo pipefail
install -d -m 0700 /var/backups/screen
sqlite3 /opt/screen/data/screen.db ".backup '/var/backups/screen/screen-$(date -u +%F).db'"
find /var/backups/screen -type f -name 'screen-*.db' -mtime +30 -delete
