#!/usr/bin/env bash
# =====================================================================
# X-08 · Prueba de restauración (RNF-09: RTO 4 h).
#
# Restaura el respaldo más reciente (o el que se indique) en una copia
# temporal, nunca sobre la base en uso, verifica su integridad, muestra
# cuántos registros tiene y mide el tiempo. Ejecutar al menos una vez al
# mes y guardar la salida como evidencia.
#
#   sudo bash deploy/probar_restauracion.sh [archivo]
# =====================================================================
set -euo pipefail
cd "$(dirname "$0")/.."
DESTINO_DIR="${DESTINO_DIR:-/var/backups/finmicro}"
ARCHIVO="${1:-$(ls -1t "$DESTINO_DIR"/finmicro_* 2>/dev/null | head -n1)}"
[ -n "$ARCHIVO" ] && [ -f "$ARCHIVO" ] || { echo "ERROR: no hay respaldos en $DESTINO_DIR" >&2; exit 1; }
INICIO=$(date +%s)
TEMPORAL="$(mktemp -d)"
trap 'rm -rf "$TEMPORAL"' EXIT
echo "Restaurando $ARCHIVO"

TABLAS="accounts_usuario finances_movimiento finances_categoria subscriptions_suscripcion core_registroauditoria"
case "$ARCHIVO" in
  *.sqlite3.gz)
    gunzip -c "$ARCHIVO" > "$TEMPORAL/restaurada.sqlite3"
    python3 - "$TEMPORAL/restaurada.sqlite3" $TABLAS <<'PY'
import sqlite3, sys
base = sqlite3.connect(sys.argv[1])
print("integrity_check:", base.execute("PRAGMA integrity_check").fetchone()[0])
for tabla in sys.argv[2:]:
    print(f"{tabla}: {base.execute(f'SELECT COUNT(*) FROM {tabla}').fetchone()[0]}")
PY
    ;;
  *.dump)
    PRUEBA="finmicro_prueba_restauracion"
    export PGHOST="${DB_HOST:-localhost}" PGPORT="${DB_PORT:-5432}" PGUSER="${DB_USER:-finmicro}" PGPASSWORD="${DB_PASSWORD:-}"
    psql -q -d postgres -c "DROP DATABASE IF EXISTS $PRUEBA;" -c "CREATE DATABASE $PRUEBA;"
    pg_restore --no-owner -d "$PRUEBA" "$ARCHIVO"
    for tabla in $TABLAS; do
      echo "$tabla: $(psql -tA -d "$PRUEBA" -c "SELECT COUNT(*) FROM $tabla;")"
    done
    psql -q -d postgres -c "DROP DATABASE $PRUEBA;"
    ;;
  *) echo "ERROR: formato desconocido: $ARCHIVO" >&2; exit 1 ;;
esac
echo "Restauración de prueba completada en $(( $(date +%s) - INICIO )) s (objetivo RNF-09: 4 h o menos)."
