"""E-mail transacional — Postmark com fallback para stub (Fase 30B3).

Quando ``POSTMARK_SERVER_TOKEN`` está vazio (dev/CI/beta inicial), o serviço
opera em **modo stub**: registra o e-mail no log e retorna sucesso, sem enviar
nada pela rede. Isso permite exercitar todo o fluxo (ex.: convites, avisos de
quota) sem dependência externa.

Em produção, defina o token; o serviço passa a usar a API HTTP do Postmark.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import Settings

logger = logging.getLogger("heillon.legal.email")

POSTMARK_API_URL = "https://api.postmarkapp.com/email"


@dataclass
class EmailResult:
    """Resultado de uma tentativa de envio."""

    sent: bool
    stubbed: bool
    detail: str


class EmailService:
    """Façade de e-mail transacional. Stateless (lê settings na construção)."""

    def __init__(self, settings: Settings) -> None:
        self._token = (settings.POSTMARK_SERVER_TOKEN or "").strip()
        self._from = settings.EMAIL_FROM
        self._enabled = bool(self._token)

    @property
    def enabled(self) -> bool:
        """True quando há token Postmark (modo real); False = stub."""
        return self._enabled

    def send(
        self,
        *,
        to: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> EmailResult:
        """Envia um e-mail. Em modo stub, apenas loga.

        Nunca lança em falha de rede — retorna ``EmailResult(sent=False, ...)``
        para que fluxos de negócio decidam o que fazer (e-mail é best-effort).
        """
        if not self._enabled:
            logger.info(
                "[email:stub] to=%s subject=%r (Postmark desativado — não enviado)",
                to,
                subject,
            )
            return EmailResult(sent=False, stubbed=True, detail="stub mode (no token)")

        try:
            import httpx

            payload = {
                "From": self._from,
                "To": to,
                "Subject": subject,
                "TextBody": text_body,
                "MessageStream": "outbound",
            }
            if html_body:
                payload["HtmlBody"] = html_body

            resp = httpx.post(
                POSTMARK_API_URL,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Postmark-Server-Token": self._token,
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                return EmailResult(sent=True, stubbed=False, detail="ok")
            logger.warning(
                "Postmark retornou %s para to=%s: %s",
                resp.status_code,
                to,
                resp.text[:200],
            )
            return EmailResult(
                sent=False, stubbed=False, detail=f"postmark {resp.status_code}"
            )
        except Exception as exc:  # noqa: BLE001 — e-mail é best-effort
            logger.warning("Falha ao enviar e-mail para %s: %s", to, exc)
            return EmailResult(sent=False, stubbed=False, detail=str(exc))
