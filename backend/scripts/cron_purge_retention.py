#!/usr/bin/env python3
"""Cron entrypoint — purga HDRs expirados por retenção de tier (F30B2).

Roda dentro do container backend (tem o app no PYTHONPATH). Usa
``RetentionService.purge_all`` que respeita ``TierLimits.retention_days``:

    free        → 30 dias
    pro         → 365 dias
    team        → 1825 dias (5 anos)
    enterprise  → nunca purga (retenção indefinida)

CRON (recomendado diário 04:00 com jitter):
    23 4 * * * docker exec heillon-backend python -m scripts.cron_purge_retention \\
        >> /var/log/heillon-retention.log 2>&1

Flags:
    --dry-run   Conta o que seria purgado mas NÃO deleta (faz rollback).
    --json      Emite resultado como JSON (para ingestão por observability).

Exit codes: 0 sucesso · 1 erro de execução.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def main() -> int:
    parser = argparse.ArgumentParser(description="Purga HDRs por retenção de tier.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Conta sem deletar (rollback ao final).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Saída em JSON.",
    )
    args = parser.parse_args()

    # Imports tardios para permitir --help sem custo de carregar settings.
    from app.core.config import get_settings
    from app.db.compat import open_connection
    from app.db.database import init_database
    from app.domain.tier.retention import RetentionService

    settings = get_settings()
    init_database(settings)

    started = datetime.now(timezone.utc).isoformat()

    try:
        if args.dry_run:
            # Abre conexão e força rollback ao final (não comita a deleção).
            from app.db.compat import resolve_dialect

            dialect = resolve_dialect(settings)
            if dialect == "postgresql":
                import psycopg2

                from app.db.compat import CompatConnection

                raw = psycopg2.connect(settings.effective_database_url)
                conn = CompatConnection(raw, dialect)
                try:
                    result = RetentionService.purge_all(conn)
                    conn.rollback()
                finally:
                    conn.close()
            else:
                import sqlite3

                from app.db.compat import CompatConnection
                from app.db.database import sqlite_file_path

                path = sqlite_file_path(settings.DATABASE_URL)
                raw = sqlite3.connect(path.as_posix(), check_same_thread=False)
                conn = CompatConnection(raw, "sqlite")
                try:
                    result = RetentionService.purge_all(conn)
                    raw.rollback()
                finally:
                    raw.close()
        else:
            with open_connection(settings) as conn:
                result = RetentionService.purge_all(conn)
    except Exception as exc:  # noqa: BLE001 — cron precisa de exit code limpo
        if args.json:
            print(
                json.dumps(
                    {"ok": False, "error": str(exc), "started_at": started},
                    ensure_ascii=False,
                )
            )
        else:
            print(f"[retention] ERRO: {exc}", file=sys.stderr)
        return 1

    payload = result.as_dict()
    payload["dry_run"] = args.dry_run

    if args.json:
        print(json.dumps({"ok": True, **payload}, ensure_ascii=False))
    else:
        mode = "DRY-RUN " if args.dry_run else ""
        print(
            f"[retention] {mode}scanned={payload['organizations_scanned']} "
            f"orgs_purged={payload['organizations_purged']} "
            f"hdrs_purged={payload['total_hdrs_purged']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
