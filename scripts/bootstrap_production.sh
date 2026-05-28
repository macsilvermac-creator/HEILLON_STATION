#!/usr/bin/env bash
# Heillon Legal — production bootstrap script.
#
# Executa após `docker compose up -d` num servidor virgem para:
#   1. Verificar que backend respondeu (curl /health 200)
#   2. Aplicar migrations (init_database roda automático no lifespan, este
#      script só confirma)
#   3. Criar a organização admin
#   4. Criar o usuário admin com senha temporária
#   5. Gerar a primeira API key (mostra plaintext UMA vez)
#   6. Rodar scripts/beta_test.py contra o servidor recém-deployado
#   7. Imprimir checklist final
#
# Uso:
#   bash scripts/bootstrap_production.sh \
#       --server https://api.heillon.com.br \
#       --admin-email admin@heillon.com.br \
#       --org-name "Heillon Legal HQ"

set -euo pipefail

SERVER=""
ADMIN_EMAIL=""
ADMIN_NAME="Administrador"
ORG_NAME=""
ORG_ID="org_admin_$(date +%s)"

while [[ $# -gt 0 ]]; do
    case $1 in
        --server) SERVER="${2:?}"; shift 2 ;;
        --admin-email) ADMIN_EMAIL="${2:?}"; shift 2 ;;
        --admin-name) ADMIN_NAME="${2:?}"; shift 2 ;;
        --org-name) ORG_NAME="${2:?}"; shift 2 ;;
        --org-id) ORG_ID="${2:?}"; shift 2 ;;
        *) echo "Flag desconhecida: $1"; exit 1 ;;
    esac
done

[[ -n "${SERVER}" ]]      || { echo "ERRO: --server obrigatório"; exit 1; }
[[ -n "${ADMIN_EMAIL}" ]] || { echo "ERRO: --admin-email obrigatório"; exit 1; }
[[ -n "${ORG_NAME}" ]]    || { echo "ERRO: --org-name obrigatório"; exit 1; }

SERVER="${SERVER%/}"
PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')"

echo
echo "============================================"
echo "  Heillon Legal — Production Bootstrap"
echo "============================================"
echo "  Servidor:    ${SERVER}"
echo "  Admin email: ${ADMIN_EMAIL}"
echo "  Org name:    ${ORG_NAME}"
echo "  Org id:      ${ORG_ID}"
echo "============================================"
echo

# ── 1. Aguardar backend healthy ───────────────────────────────────────────────
echo "[1/6] Aguardando backend ficar healthy..."
for attempt in {1..30}; do
    if curl -fsS --max-time 5 "${SERVER}/health" > /dev/null 2>&1; then
        echo "      ✓ Backend healthy"
        break
    fi
    echo "      Tentativa ${attempt}/30 — aguardando 3s..."
    sleep 3
done

curl -fsS "${SERVER}/health" > /dev/null || { echo "ERRO: /health não respondeu em 90s"; exit 1; }

# ── 2. Criar organização + usuário admin via /auth/register ──────────────────
echo
echo "[2/6] Criando usuário admin..."

REG_RESPONSE=$(curl -fsS -X POST "${SERVER}/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "$(cat <<EOF
{
    "email": "${ADMIN_EMAIL}",
    "name": "${ADMIN_NAME}",
    "password": "${PASSWORD}",
    "role": "admin",
    "organization_id": "${ORG_ID}"
}
EOF
)")

USER_ID=$(echo "${REG_RESPONSE}" | python3 -c 'import sys,json; print(json.load(sys.stdin)["user"]["user_id"])')
echo "      ✓ Usuário criado: ${USER_ID}"

# ── 3. Obter JWT cookie ───────────────────────────────────────────────────────
echo
echo "[3/6] Autenticando..."
COOKIE_JAR="$(mktemp)"
trap "rm -f ${COOKIE_JAR}" EXIT

curl -fsS -c "${COOKIE_JAR}" -X POST "${SERVER}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${PASSWORD}\"}" \
    > /dev/null

echo "      ✓ Autenticado (cookie em ${COOKIE_JAR})"

# ── 4. Gerar primeira API key ─────────────────────────────────────────────────
echo
echo "[4/6] Gerando primeira API key..."

KEY_RESPONSE=$(curl -fsS -b "${COOKIE_JAR}" -X POST "${SERVER}/api/v1/me/api-keys" \
    -H "Content-Type: application/json" \
    -d '{"name":"Bootstrap key (gerada por bootstrap_production.sh)"}')

API_KEY=$(echo "${KEY_RESPONSE}" | python3 -c 'import sys,json; print(json.load(sys.stdin)["plaintext_key"])')
KEY_ID=$(echo "${KEY_RESPONSE}" | python3 -c 'import sys,json; print(json.load(sys.stdin)["api_key_id"])')

echo "      ✓ API key gerada: ${KEY_ID}"

# ── 5. Validar via beta_test.py ───────────────────────────────────────────────
echo
echo "[5/6] Validando com beta_test.py..."

if [[ -f "$(dirname "$0")/beta_test.py" ]]; then
    python3 "$(dirname "$0")/beta_test.py" \
        --server "${SERVER}" \
        --api-key "${API_KEY}" \
        --report-path "/tmp/bootstrap_validation.json" || {
        echo "      ⚠ beta_test.py reportou falhas — revise /tmp/bootstrap_validation.json"
    }
else
    echo "      AVISO: beta_test.py não encontrado — pulando validação"
fi

# ── 6. Output final ───────────────────────────────────────────────────────────
echo
echo "============================================"
echo "  ✓ BOOTSTRAP CONCLUÍDO"
echo "============================================"
echo
echo "  GUARDE ESTAS INFORMAÇÕES (mostradas APENAS uma vez):"
echo
echo "  Organização ID:    ${ORG_ID}"
echo "  Admin user ID:     ${USER_ID}"
echo "  Admin email:       ${ADMIN_EMAIL}"
echo "  Admin password:    ${PASSWORD}"
echo "  Primeira API key:  ${API_KEY}"
echo
echo "  Próximos passos:"
echo "  1. Faça login no console em ${SERVER//api/console} com email + senha"
echo "  2. Mude a senha em /conta/perfil"
echo "  3. Use a API key acima para configurar a extensão / gateway"
echo "  4. Comece a enviar os convites do beta (ver INVITE_EMAIL.md)"
echo
echo "============================================"
