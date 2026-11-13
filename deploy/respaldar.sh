#!/usr/bin/env bash
# =====================================================================
# X-08 · Respaldo diario de la base de datos de FinMicro (RNF-09: RPO 24 h).
#
# - SQLite (hoy en la EC2): copia en caliente con la API de respaldo de
#   SQLite, verifica su integridad y la comprime.
# - PostgreSQL (DB_ENGINE=postgresql): pg_dump en formato custom y
#   verificación con pg_restore --list. Requiere postgresql-client.
# Si S3_BUCKET está definido, sube el respaldo cifrado a S3 (AWS CLI).
# Conserva DIAS_RETENCION días de respaldos locales (14 por omisión).
#
# Uso en el servidor (como root, desde cron; ver deploy/crontab.txt):
#   sudo bash deploy/respaldar.sh
# Variables: se leen del entorno o, si faltan, del archivo .env.
# =====================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

leer_env() {  # leer_env CLAVE: valor del entorno o, si no, del .env (sin ejecutarlo)
  local valor="${!1:-}"
  if [ -z "$valor" ] && [ -f "${ENV_FILE:-.env}" ]; then
    valor="$(grep -E "^$1=" "${ENV_FILE:-.env}" | tail -n1 | cut -d= -f2-)"
  fi
  printf '%s' "$valor"
}

DESTINO_DIR="${DESTINO_DIR:-/var/backups/finmicro}"
DIAS_RETENCION="${DIAS_RETENCION:-14}"
SQLITE_PATH="${SQLITE_PATH:-/var/lib/docker/volumes/finmicro_finmicro_datos/_data/db.sqlite3}"
MOTOR="$(leer_env DB_ENGINE)"
S3_BUCKET="$(leer_env S3_BUCKET)"
SELLO="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DESTINO_DIR"
chmod 700 "$DESTINO_DIR"

if [ "$MOTOR" = "postgresql" ]; then
  ARCHIVO="$DESTINO_DIR/finmicro_${SELLO}.dump"
  PUERTO="$(leer_env DB_PORT)"
  PGPASSWORD="$(leer_env DB_PASSWORD)" pg_dump --format=custom --no-owner \
    -h "$(leer_env DB_HOST)" -p "${PUERTO:-5432}" \
    -U "$(leer_env DB_USER)" -d "$(leer_env DB_NAME)" -f "$ARCHIVO"
  pg_restore --list "$ARCHIVO" > /dev/null
else
  [ -r "$SQLITE_PATH" ] || { echo "ERROR: no se puede leer $SQLITE_PATH" >&2; exit 1; }
  ARCHIVO="$DESTINO_DIR/finmicro_${SELLO}.sqlite3"
  python3 - "$SQLITE_PATH" "$ARCHIVO" <<'PY'
import sqlite3, sys
origen, destino = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
with destino:
    origen.backup(destino)   # copia consistente aunque la app esté escribiendo
resultado = destino.execute("PRAGMA integrity_check").fetchone()[0]
destino.close()
if resultado != "ok":
    sys.exit(f"ERROR: el respaldo no pasó integrity_check: {resultado}")
PY
  gzip "$ARCHIVO"
  ARCHIVO="$ARCHIVO.gz"
fi

# Un respaldo vacío es peor que ninguno.
[ -s "$ARCHIVO" ] || { echo "ERROR: respaldo vacío: $ARCHIVO" >&2; exit 1; }
chmod 600 "$ARCHIVO"

if [ -n "$S3_BUCKET" ]; then
  aws s3 cp "$ARCHIVO" "s3://$S3_BUCKET/diario/$(basename "$ARCHIVO")" --sse AES256 --only-show-errors
fi
find "$DESTINO_DIR" -name 'finmicro_*' -type f -mtime "+$DIAS_RETENCION" -delete
echo "$(date -Is) respaldo OK: $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))${S3_BUCKET:+ · copiado a s3://$S3_BUCKET/diario/}"
