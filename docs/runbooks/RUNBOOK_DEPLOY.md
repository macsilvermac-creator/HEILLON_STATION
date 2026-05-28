# Runbook: Deploy seguro em produção

> Como subir o Heillon Station do zero ou aplicar uma nova versão sem
> downtime. Tempo total estimado: **20-30 minutos** para deploy do zero,
> **3-5 minutos** para release subsequente.

---

## Pré-requisitos do servidor

- VPS com Docker 24+ + Docker Compose v2
- Domínios apontando para o IP do servidor:
  - `api.heillon.com.br` (backend)
  - `verify.heillon.com.br` (verificação pública, recomendado separado para CDN)
- Portas 80 e 443 abertas no firewall
- Acesso SSH com chave (não senha)
- ~10 GB de espaço livre no disco

---

## 1. Deploy do zero (primeira vez)

### 1.1. Conectar e preparar diretório
```bash
ssh deploy@vps.heillon.com.br
sudo mkdir -p /opt/heillon
sudo chown $USER:$USER /opt/heillon
cd /opt/heillon
git clone https://github.com/<seu-org>/heillon-legal.git .
```

### 1.2. Gerar secrets e popular .env de produção
```bash
cat > .env <<'EOF'
# ── Secrets críticos (gerar com os comandos abaixo) ────────────
POSTGRES_PASSWORD=...
AUTH_SECRET_KEY=...
FERNET_ENCRYPTION_KEY=...
HEILLON_ADMIN_TOKEN=...

# ── Domínios ───────────────────────────────────────────────────
VERIFICATION_PUBLIC_BASE=https://api.heillon.com.br
FRONTEND_PUBLIC_ORIGIN=https://console.heillon.com.br
DOMAIN_EMAIL=ops@heillon.com.br

# ── Opcionais (recomendados em produção) ───────────────────────
BILLING_WEBHOOK_SECRET=...
SENTRY_DSN=
B2_BUCKET=
B2_KEY_ID=
B2_APP_KEY=
BACKUP_ENCRYPTION_KEY=
EOF

chmod 600 .env
```

Comandos para gerar cada secret:
```bash
# POSTGRES_PASSWORD (24 chars)
python3 -c 'import secrets; print(secrets.token_urlsafe(18))'

# AUTH_SECRET_KEY (>= 32 chars)
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'

# FERNET_ENCRYPTION_KEY
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'

# HEILLON_ADMIN_TOKEN
python3 -c 'import secrets; print(secrets.token_urlsafe(36))'

# BILLING_WEBHOOK_SECRET (se for usar webhooks da plataforma de pagamento)
python3 -c 'import secrets; print(secrets.token_hex(32))'

# BACKUP_ENCRYPTION_KEY (criptografia em repouso dos dumps)
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### 1.3. Subir o stack
```bash
docker compose \
    -f docker-compose.prod.yml \
    -f docker-compose.caddy.yml \
    up -d --build
```

Aguarde ~30 segundos. Acompanhe:
```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

### 1.4. Validar
```bash
# Health do backend
curl https://api.heillon.com.br/health
# Esperado: {"status":"ok","version":"12.0","timestamp":"..."}

# Readiness (DB + Redis)
curl https://api.heillon.com.br/health/ready
# Esperado: {"status":"ready","checks":{"database":{"status":"ok"},...}}
```

### 1.5. Bootstrap inicial (cria org + admin + primeira API key)
```bash
bash scripts/bootstrap_production.sh \
    --server https://api.heillon.com.br \
    --admin-email ops@heillon.com.br \
    --admin-name "Operações Heillon" \
    --org-name "Heillon Legal HQ"
```

**ANOTE** a senha temporária e a API key que aparecem na saída — **não serão mostradas de novo**.

### 1.6. Agendar backup diário
```bash
sudo crontab -e
```
Adicione (com jitter aleatório de minutos para reduzir contenção):
```cron
17 3 * * * /opt/heillon/scripts/backup_postgres.sh >> /var/log/heillon-backup.log 2>&1
```

### 1.7. Validar com beta_test.py
```bash
python3 scripts/beta_test.py \
    --server https://api.heillon.com.br \
    --api-key <sua-primeira-chave>
```

Esperado: **7/7 testes OK**. Se algum falhar, ver `Runbook: Incidente`.

---

## 2. Deploy de nova versão (subsequente)

Padrão **migrate-then-deploy** com zero downtime para mudanças backward-compatible:

```bash
cd /opt/heillon
git fetch origin
git checkout <tag-ou-commit-novo>

# Build da imagem nova sem subir
docker compose -f docker-compose.prod.yml build backend

# Pull-restart só do backend (Postgres + Redis permanecem)
docker compose -f docker-compose.prod.yml up -d --no-deps backend

# Acompanhar saúde
watch -n 2 'curl -sf https://api.heillon.com.br/health/ready | jq'
```

A inicialização do backend roda `init_database()` no lifespan, que aplica
migrations automaticamente. Para mudanças que QUEBRAM esquema antigo
(remover coluna, mudar tipo), siga o padrão expand-contract:
- Release N: adiciona coluna nova, dual-write
- Release N+1: aplica migrate data
- Release N+2: remove coluna antiga

---

## 3. Rollback

Se o novo release apresentar problemas em 5 minutos:

```bash
cd /opt/heillon
git checkout <tag-anterior-estável>
docker compose -f docker-compose.prod.yml up -d --no-deps backend
```

Se houve mudança de schema irreversível, restaure o backup mais recente
(ver `RUNBOOK_BACKUP.md`).

---

## 4. Monitorar pós-deploy

Os primeiros 30 minutos após deploy são críticos. Cheque:

- **Sentry**: nenhum spike de erros vs baseline
- **Better Stack uptime**: continua verde
- **`/api/v1/admin/beta-metrics`**: HDRs/24h continua subindo
- **Logs**: `docker logs -f backend | grep -i "error\|critical"`

---

## 5. Comandos úteis

| Comando | Função |
|---|---|
| `docker compose -f docker-compose.prod.yml ps` | Status dos containers |
| `docker compose -f docker-compose.prod.yml logs -f backend` | Logs streaming |
| `docker compose -f docker-compose.prod.yml exec backend bash` | Shell no container |
| `docker compose -f docker-compose.prod.yml exec postgres psql -U heillon` | psql direto |
| `docker compose -f docker-compose.prod.yml restart backend` | Restart limpo |
| `docker system prune -af` | Limpar imagens antigas |
