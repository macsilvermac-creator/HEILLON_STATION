# Runbook: Backup e Restauração

> Estratégia de backup do Heillon Station + procedimento de restauração.
> RTO (Recovery Time Objective): **< 30 minutos** · RPO (Recovery Point
> Objective): **< 24 horas** com backup diário; **< 1 hora** com WAL streaming.

---

## O que é backupado

| Camada | Conteúdo | Método | Frequência |
|---|---|---|---|
| **PostgreSQL** | Todas as tabelas: usuários, orgs, HDRs, missions, frameworks | `pg_dump -F c` | Diário 03:17 UTC |
| **HDR PDFs (forensic packages)** | PDFs/A-3 gerados | `rsync` para R2/B2 | Diário 04:00 UTC (script futuro) |
| **Configuração `.env`** | Secrets em produção | Manual no Doppler/Vault | Quando muda |
| **Logs estruturados** | stdout dos containers | Logtail/Loki (se configurado) | Stream contínuo |
| **Certificados TLS** | Caddy/Let's Encrypt | Volume `caddy_data` | Automático |

---

## 1. Backup automático (já configurado)

Script: `scripts/backup_postgres.sh`
Cron: `17 3 * * * /opt/heillon/scripts/backup_postgres.sh`
Log: `/var/log/heillon-backup.log`

### Como funciona

1. `pg_dump -F c -Z 6` (formato custom, compressão nível 6) dentro do container
2. Copia dump para `/var/backups/heillon/` no host
3. Se `BACKUP_ENCRYPTION_KEY` set: AES-256-CBC com PBKDF2
4. Se `B2_BUCKET` ou `S3_BUCKET` set: upload para storage remoto
5. Retém últimos `BACKUP_RETENTION_DAYS=30` localmente, rota o resto

### Validar que está rodando

```bash
# Ver últimos backups
ls -lh /var/backups/heillon/

# Ver log
tail -50 /var/log/heillon-backup.log

# Ver cron
sudo crontab -l | grep heillon
```

### Verificar integridade de um backup

```bash
# pg_restore --list lê o catálogo sem aplicar — falha se corrupto
docker exec heillon-legal-postgres-1 \
    pg_restore --list /var/backups/heillon/heillon_2026-05-27_031700.dump | head -20
```

---

## 2. Backup ad-hoc (antes de operação arriscada)

```bash
# Antes de aplicar migration potencialmente destrutiva
bash scripts/backup_postgres.sh

# Verifica saída — deve aparecer "Backup concluído com sucesso"
```

---

## 3. Restauração (DR — disaster recovery)

### Cenário A — Banco corrompeu mas servidor está ok

```bash
# 1. Parar a aplicação (mantém Postgres)
docker compose -f docker-compose.prod.yml stop backend

# 2. Identificar o backup mais recente
ls -lt /var/backups/heillon/ | head -5

# 3. Restaurar (script faz o pg_restore --clean automaticamente)
bash scripts/backup_postgres.sh --restore /var/backups/heillon/heillon_<TIMESTAMP>.dump

# 4. Subir backend
docker compose -f docker-compose.prod.yml up -d backend

# 5. Validar
curl https://api.heillon.com.br/health/ready
```

### Cenário B — VPS perdido / migrar para servidor novo

```bash
# No servidor NOVO:
# 1. Provisionar servidor + Docker (RUNBOOK_DEPLOY.md seção 1.1)
# 2. Restaurar .env do Doppler/Vault/cofre
# 3. Clonar repo + checkout da tag em produção

# 4. Baixar backup do storage remoto
b2 download-file-by-name heillon-backups postgres/heillon_<TIMESTAMP>.dump.enc /tmp/restore.dump.enc

# 5. Subir Postgres SEM o backend
docker compose -f docker-compose.prod.yml up -d postgres
sleep 15  # aguardar healthcheck

# 6. Restaurar
bash scripts/backup_postgres.sh --restore /tmp/restore.dump.enc

# 7. Subir resto do stack
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml up -d

# 8. Atualizar DNS (api.heillon.com.br → novo IP)
# 9. Validar
curl https://api.heillon.com.br/health/ready
python3 scripts/beta_test.py --server https://api.heillon.com.br --api-key <chave>
```

### Cenário C — Restauração parcial (uma tabela específica)

Útil se um bug apagou só missões/HDRs de uma org sem afetar resto.

```bash
# 1. Restaurar dump em um Postgres temporário
docker run --rm -d --name pg_temp -e POSTGRES_PASSWORD=temp postgres:16-alpine
sleep 10
docker cp /var/backups/heillon/heillon_<TIMESTAMP>.dump pg_temp:/tmp/dump
docker exec pg_temp pg_restore --clean --if-exists -U postgres -d postgres /tmp/dump

# 2. Extrair só a tabela necessária
docker exec pg_temp pg_dump -U postgres -d postgres -t hdrs --data-only > /tmp/hdrs_only.sql

# 3. Aplicar no Postgres de produção
docker compose -f docker-compose.prod.yml exec -T postgres psql -U heillon -d heillon < /tmp/hdrs_only.sql

# 4. Limpar
docker stop pg_temp
```

---

## 4. Teste de restauração (mensal — OBRIGATÓRIO)

**Backup não testado = backup que não existe.**

Agendar primeira segunda do mês:

```bash
# 1. Criar VPS efêmero (DigitalOcean droplet R$ 20 ou local Docker)
# 2. Restaurar backup mais recente nele
# 3. Subir backend apontando para esse Postgres
# 4. Rodar beta_test.py
# 5. Documentar: tempo de restauração, % de testes OK, qualquer dado faltante
# 6. Apagar o VPS efêmero
```

Manter histórico em `docs/dr_drills/YYYY-MM.md`.

---

## 5. Estratégias de melhoria futura

| Quando | Upgrade |
|---|---|
| > 100 GB DB | WAL archiving (`pg_basebackup` + `archive_command`) → RPO < 1h |
| > 1 TB DB | Streaming replication → standby quente |
| > 5 TB DB | Migrar para managed (RDS, Cloud SQL, Supabase) com PITR |
| Multi-região | Replicação cross-region + DNS failover |

Para o Heillon hoje (Beta + GA inicial), backup diário + retenção 30d em
storage remoto é suficiente.
