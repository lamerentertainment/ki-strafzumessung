#!/bin/bash
#
# sync_to_staging.sh
#
# Dieses Skript automatisiert die Synchronisation der lokalen PostgreSQL-Datenbank
# mit der Staging-Datenbank.
#
# Ablauf:
# 1. Erstellt einen sauberen Dump der lokalen Datenbank 'kizumessung' (updated.sql).
# 2. Spielt den Dump in die Remote-Staging-Datenbank ein.
# 3. Bereinigt die temporär erstellte 'updated.sql' Datei.
#
# Verwendung:
#   ./sync_to_staging.sh
#

# Bei Fehlern sofort abbrechen
set -e

# Konfiguration
LOCAL_DB="kizumessung"
STAGING_DB_URL="postgresql://hufpnewbqkwupivf:dephbdpwfrsoysrw@157.90.148.142:8001/vbganpmfiwgvxqjg"
DUMP_FILE="updated.sql"

echo "=== Starte Datenbank-Synchronisation (Lokal -> Staging) ==="

# 1. Lokalen Dump erstellen
echo "[1/3] Erstelle Dump der lokalen Datenbank '$LOCAL_DB'..."
pg_dump --clean --no-privileges "$LOCAL_DB" > "$DUMP_FILE"

# 2. Dump auf Staging einspielen
echo "[2/3] Spiele Dump in die Staging-Datenbank ein..."
psql "$STAGING_DB_URL" < "$DUMP_FILE"

# 3. Aufräumen
echo "[3/3] Lösche temporäre Dump-Datei '$DUMP_FILE'..."
rm "$DUMP_FILE"

echo "=== Synchronisation erfolgreich abgeschlossen! ==="
