#!/usr/bin/env bash
# Heillon Legal — PostgreSQL backup script (rotação + criptografia opcional + upload S3/B2).
#
# Roda dentro do host (não dentro do container) e usa docker exec para gerar
# o pg_dump custom-format. Mantém últimos 30 dias localmente + envia para
# storage remoto (Cloudflare R2 / Backblaze B2 / S3).
#
# CRON (recomendado diário 03:00 com jitter):
#   17 3 * * * /opt/heillon/scripts/backup_postgres.sh >> /var/log/heillon-backup.log 2>&1
#
# Restauração:
#   bash scripts/backup_postgres.sh --restore /caminho/para/backup.dump.gz
#
# Variáveis de ambiente:
#   BACKUP_DIR             local dir (default: /var/backups/heillon)
#   BACKUP_RETENTION_DAYS  default: 30
#   BACKUP_ENCRYPTION_KEY  opcional — quando set, criptografa com openssl AES-256-CBC
#   B2_BUCKET / S3_BUCKET  destino remoto (mutuamente exclusivos)
#   B2_KEY_ID / B2_APP_KEY ou AWS_ACCESS_KEY_ID/SECRET — credenciais
#   POSTGRES_CONTAINER     nome do container (default: heillon-legal-postgres-1)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/heillon}"
RETENTION="${BACKUP_RETENTION_DAYS:-30}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-heillon-legal-postgres-1}"
DATE="$(date +%Y-%m-%d_%H%M%S)"
DUMP_NAME="heillon_${DATE}.dump"
LOG_TAG="[heillon-backup]"

log() {
    echo "${LOG_TAG} $(date +%Y-%m-%dT%H:%M:%S%z) — $*"
}

# ── Restore mode ──────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--restore" ]]; then
    SOURCE="${2:?Forneça caminho do .dump ou .dump.enc}"
    log "RESTAURANDO de ${SOURCE} — isso VAI SUBSTITUIR o banco atual."
    read -rp "Digite 'restaurar' para confirmar: " CONFIRM
    [[ "${CONFIRM}" == "restaurar" ]] || { log "Abortado."; exit 1; }

    TMP_DUMP="/tmp/heillon_restore_${DATE}.dump"
    if [[ "${SOURCE}" == *.enc ]]; then
        [[ -n "${BACKUP_ENCRYPTION_KEY:-}" ]] || { log "BACKUP_ENCRYPTION_KEY necessário para .enc"; exit 1; }
        log "Decriptando ${SOURCE}..."
        openssl enc -d -aes-256-cbc -pbkdf2 -in "${SOURCE}" -out "${TMP_DUMP}" -pass "env:BACKUP_ENCRYPTION_KEY"
    elif [[ "${SOURCE}" == *.gz ]]; then
        gunzip -c "${SOURCE}" > "${TMP_DUMP}"
    else
        cp "${SOURCE}" "${TMP_DUMP}"
    fi

    log "Aplicando pg_restore no container ${POSTGRES_CONTAINER}..."
    docker exec -i "${POSTGRES_CONTAINER}" \
        pg_restore --clean --if-exists --no-owner --no-acl -U heillon -d heillon < "${TMP_DUMP}"
    rm -f "${TMP_DUMP}"
    log "Restore concluído. Verifique a aplicação."
    exit 0
fi

# ── Backup mode ───────────────────────────────────────────────────────────────
mkdir -p "${BACKUP_DIR}"
LOCAL_PATH="${BACKUP_DIR}/${DUMP_NAME}"

log "Iniciando pg_dump (formato custom)..."
docker exec "${POSTGRES_CONTAINER}" \
    pg_dump -U heillon -F c -Z 6 -f /tmp/dump heillon
docker cp "${POSTGRES_CONTAINER}:/tmp/dump" "${LOCAL_PATH}"
docker exec "${POSTGRES_CONTAINER}" rm -f /tmp/dump

# Tamanho + integridade básica
SIZE=$(stat -c %s "${LOCAL_PATH}" 2>/dev/null || stat -f %z "${LOCAL_PATH}")
log "Dump local: ${LOCAL_PATH} (${SIZE} bytes)"

if [[ "${SIZE}" -lt 1024 ]]; then
    log "ERRO: dump muito pequeno (<1KB) — possível falha. Abortando upload."
    exit 1
fi

# ── Criptografia opcional ─────────────────────────────────────────────────────
UPLOAD_PATH="${LOCAL_PATH}"
if [[ -n "${BACKUP_ENCRYPTION_KEY:-}" ]]; then
    UPLOAD_PATH="${LOCAL_PATH}.enc"
    log "Criptografando com AES-256-CBC..."
    openssl enc -aes-256-cbc -pbkdf2 -salt -in "${LOCAL_PATH}" -out "${UPLOAD_PATH}" -pass "env:BACKUP_ENCRYPTION_KEY"
    rm -f "${LOCAL_PATH}"
    LOCAL_PATH="${UPLOAD_PATH}"
fi

# ── Upload S3 / B2 ────────────────────────────────────────────────────────────
upload_b2() {
    log "Upload para Backblaze B2 (${B2_BUCKET})..."
    if ! command -v b2 &>/dev/null; then
        log "AVISO: b2 CLI não instalado — pulando upload."
        log "       Instale com: pip install b2"
        return 0
    fi
    b2 authorize-account "${B2_KEY_ID}" "${B2_APP_KEY}"
    b2 upload-file "${B2_BUCKET}" "${UPLOAD_PATH}" "postgres/$(basename ${UPLOAD_PATH})"
}

upload_s3() {
    log "Upload para S3 (${S3_BUCKET})..."
    if ! command -v aws &>/dev/null; then
        log "AVISO: aws CLI não instalado — pulando upload."
        return 0
    fi
    aws s3 cp "${UPLOAD_PATH}" "s3://${S3_BUCKET}/postgres/$(basename ${UPLOAD_PATH})"
}

if [[ -n "${B2_BUCKET:-}" ]]; then
    upload_b2
elif [[ -n "${S3_BUCKET:-}" ]]; then
    upload_s3
else
    log "Nenhum storage remoto configurado (B2_BUCKET / S3_BUCKET) — backup ficará apenas local."
fi

# ── Rotação local ─────────────────────────────────────────────────────────────
log "Rotacionando backups locais com mais de ${RETENTION} dias..."
find "${BACKUP_DIR}" -name "heillon_*.dump*" -type f -mtime "+${RETENTION}" -delete

log "Backup concluído com sucesso: ${UPLOAD_PATH}"
