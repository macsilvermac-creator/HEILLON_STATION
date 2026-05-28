# Runbook: Resposta a Incidente

> Como reagir quando algo dá errado em produção. Tempo de resposta-alvo
> (SLA interno): **5 minutos** para acknowledgment, **30 minutos** para
> contenção, **2 horas** para resolução em incidentes médios.

---

## Severidades

| Sev | Definição | Exemplo | Ação |
|---|---|---|---|
| **SEV1** | Sistema fora do ar OU vazamento de dados | Backend 502 generalizado, DB corrompido, vazamento de chave | Acordar todos, status page imediato |
| **SEV2** | Funcionalidade crítica quebrada para subset | Gateway 500 para 50% dos requests, extensão não captura mais | Avisar canal, contenção em 1h |
| **SEV3** | Funcionalidade não-crítica degradada | Verificação pública lenta, dashboard admin com lag | Próximo dia útil |

---

## Checklist primeira resposta (qualquer SEV)

1. **Ack o alerta** (Sentry, Better Stack, ou usuário reportou) em < 5 min.
2. **Abrir incidente no canal interno** (#incidentes Discord/Slack) com:
   - Hora do alerta
   - Severidade estimada
   - Sintoma observado
3. **Atualizar status page** se SEV1 ou SEV2 (Better Stack auto-detecta;
   pode acelerar com nota manual).
4. **Capturar evidência** ANTES de mexer:
   ```bash
   # Logs recentes do backend (últimos 5 min)
   docker compose -f docker-compose.prod.yml logs --since 5m backend > /tmp/incident_$(date +%s).log

   # Snapshot Sentry (issue ID + breadcrumbs)
   # → copiar URL do Sentry no canal

   # Métricas do momento
   curl -s -H "X-Heillon-Admin-Token: ${ADMIN_TOKEN}" \
        https://api.heillon.com.br/api/v1/admin/beta-metrics > /tmp/metrics_$(date +%s).json
   ```

---

## Cenário 1 — Backend não responde (5xx ou timeout)

### Diagnóstico
```bash
# 1. Health do processo
curl -v https://api.heillon.com.br/health
# Sem resposta → backend caiu ou proxy caiu
# 200 OK mas /health/ready 503 → deps caíram

# 2. Status containers
docker compose -f docker-compose.prod.yml ps
# Look for: not "Up" or "Restarting"

# 3. Memória / disco
free -h ; df -h
```

### Ações
- Se container `backend` está `Restarting`: ver logs (`docker logs --tail 100 backend`); provavelmente crashou no lifespan.
- Se disco cheio (`/var/lib/docker` > 90%): `docker system prune -af` e `journalctl --vacuum-size=200M`
- Se memória < 200MB: matar processos não-essenciais; considerar upgrade do VPS
- Se Postgres caiu: ver Cenário 2

### Restart seguro
```bash
docker compose -f docker-compose.prod.yml restart backend
sleep 10
curl https://api.heillon.com.br/health/ready
```

---

## Cenário 2 — Postgres não responde

### Diagnóstico
```bash
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U heillon
# Esperado: "accepting connections"

# Se falhou:
docker compose -f docker-compose.prod.yml logs postgres | tail -100
```

### Ações
- Se Postgres não inicia: ver últimos logs por erro de corrupção
- Se erro de corrupção:
  1. **Não** mexa em `/var/lib/postgresql/data` direto
  2. Pare o Postgres: `docker compose stop postgres`
  3. Restaure backup mais recente (ver `RUNBOOK_BACKUP.md` seção "Restaurar")
  4. Suba: `docker compose up -d postgres`
- Se disco cheio: idem cenário 1
- Se OOM kill: aumentar limits ou upgrade VPS

---

## Cenário 3 — Redis não responde

### Diagnóstico
```bash
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
# Esperado: PONG
```

### Impacto
- Rate limiting cai para in-memory fallback (já implementado em F23A) → funcional mas perde precisão entre workers
- JWT revocation falha silenciosamente (graceful, novos logins continuam funcionando)

### Ação
```bash
docker compose -f docker-compose.prod.yml restart redis
```

Não é SEV1 — sistema funciona degradado.

---

## Cenário 4 — Vazamento ou comprometimento de chave

### Imediato (< 5 min)
1. **Identificar qual chave**: AUTH_SECRET_KEY? FERNET? API key de usuário?
2. **Revogar/rotacionar imediatamente**:
   - API key de usuário: `DELETE /api/v1/me/api-keys/{id}` ou direto no DB
   - AUTH_SECRET_KEY:
     ```bash
     # Gerar nova
     NEW_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
     # Editar .env, atualizar AUTH_SECRET_KEY, restart backend
     # ATENÇÃO: invalida TODOS os JWTs ativos → usuários precisam logar de novo
     ```
   - FERNET: ver `RUNBOOK_ROTACAO_FERNET.md` (rotação sem downtime via key ring)
3. **Auditar últimas 24h** de uso da chave comprometida no DB
4. **Notificar afetados** se foi chave de cliente

### Pós-incidente (< 24h)
- Documentar timeline detalhado
- Notificar ANPD se houver risco a dados pessoais (LGPD art. 48, 72h SLA)
- Revisão de causa raiz (RCA)

---

## Cenário 5 — Quota free aparenta estar vazando

Sintomas: usuários free reportam "criei só X HDRs e diz que excedeu Y > limit".

### Diagnóstico
```bash
# Ver quota state do usuário
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.core.config import get_settings
from app.db.compat import open_connection
from app.domain.tier.services import QuotaService

with open_connection(get_settings()) as conn:
    snap = QuotaService.snapshot(conn, organization_id='org_abc')
    print(snap.model_dump_json(indent=2))
"
```

### Causa provável
- `tier_period_start` ficou em 1970 (sentinel) e backfill não rolou
- Job de rollover não acontece (período expirou mas não resetou)

### Fix temporário
```sql
-- Conectar via docker exec ... psql
UPDATE organizations
SET tier_period_start = NOW(),
    tier_period_end = NOW() + INTERVAL '30 days'
WHERE organization_id = 'org_xyz';
```

---

## Cenário 6 — TSA não responde / timestamps inválidos

### Diagnóstico
```bash
# Endpoint freetsa
curl -v https://freetsa.org/tsr

# Status Serpro / Certisign — checar página de status do provider
```

### Impacto
- Novos HDRs não terão `timestamp_trusted` válido
- HDRs antigos continuam verificáveis
- Sistema CONTINUA funcionando — TSA falha não bloqueia request

### Mitigação
- Trocar `TSA_PROVIDER` para fallback (de Serpro para Certisign por exemplo)
- Avisar usuários que selo qualificado não está sendo aplicado por X horas
- Re-emitir timestamps qualificados retroativamente quando TSA voltar
  (script futuro: `scripts/reissue_timestamps.py`)

---

## Cenário 7 — Spike inesperado de tráfego / DDoS

### Diagnóstico
```bash
# Conexões abertas no host
ss -s

# Requests/s no Caddy
docker logs caddy | tail -1000 | wc -l
```

### Ações
- **Cloudflare** em "I'm Under Attack" mode imediatamente (5 min de captcha para todos)
- Banir IPs abusivos via firewall do host (`iptables` ou `ufw`)
- Aumentar `WEB_CONCURRENCY` se memória permitir
- Considerar mover para tier maior do VPS temporariamente

---

## Checklist pós-incidente (RCA)

Dentro de 48h após resolução:

- [ ] Timeline detalhado: alerta → ack → contenção → resolução
- [ ] Causa raiz identificada (5-whys)
- [ ] Ação correctiva implementada (não só workaround)
- [ ] Monitor ou alerta novo criado para detectar recorrência
- [ ] Documentado em `docs/postmortem_YYYY-MM-DD.md`
- [ ] Comunicado aos clientes afetados (se aplicável)
- [ ] Notificado ANPD (se aplicável, LGPD art. 48)
- [ ] Atualizado este runbook se cenário novo
