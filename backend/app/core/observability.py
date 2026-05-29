"""Observability bootstrap — Sentry (opcional) (Fase 30B3).

Sentry é estritamente opcional:
  * Se ``SENTRY_DSN`` estiver vazio → não faz nada (zero overhead).
  * Se ``sentry-sdk`` não estiver instalado → loga aviso e segue (não quebra).

Mantemos o SDK como dependência opcional para não pesar o ambiente de
desenvolvimento/CI. Em produção, instale ``sentry-sdk`` e defina o DSN.
"""

from __future__ import annotations

import logging

from app.core.config import Settings

logger = logging.getLogger("heillon.legal.observability")

_initialized = False


def init_sentry(settings: Settings) -> bool:
    """Inicializa o Sentry se configurado. Retorna True se ativado.

    Idempotente: chamadas repetidas (ex.: testes recriando o app) não
    re-inicializam.
    """
    global _initialized

    dsn = (settings.SENTRY_DSN or "").strip()
    if not dsn:
        return False

    if _initialized:
        return True

    try:
        import sentry_sdk
    except ImportError:
        logger.warning(
            "SENTRY_DSN definido mas 'sentry-sdk' não está instalado — "
            "monitoramento de erros DESATIVADO. Instale com: pip install sentry-sdk"
        )
        return False

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            # Não enviar PII por padrão — HDRs contêm dados sensíveis.
            send_default_pii=False,
        )
        _initialized = True
        logger.info(
            "Sentry inicializado (env=%s, traces=%.2f)",
            settings.ENVIRONMENT,
            settings.SENTRY_TRACES_SAMPLE_RATE,
        )
        return True
    except Exception as exc:  # noqa: BLE001 — observability nunca deve derrubar o app
        logger.warning("Falha ao inicializar Sentry: %s", exc)
        return False
