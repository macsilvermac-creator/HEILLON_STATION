"use client";

/**
 * CookieConsent — banner LGPD de consentimento de cookies (F30B2).
 *
 * Política de privacidade do produto: usamos APENAS cookies estritamente
 * necessários (sessão autenticada HttpOnly). Não há cookies de marketing nem
 * rastreamento de terceiros dentro do sistema. Por isso o banner é informativo
 * + permite recusar o que é opcional (atualmente nada além do essencial),
 * registrando a escolha do titular localmente.
 *
 * A escolha é persistida em localStorage para não reaparecer a cada navegação.
 * Não enviamos nada a terceiros; é puramente uma camada de transparência LGPD.
 */

import Link from "next/link";
import { useEffect, useState } from "react";

const CONSENT_STORAGE_KEY = "heillon_cookie_consent";
const CONSENT_VERSION = "1"; // bump para re-pedir consentimento após mudança material

type ConsentChoice = "accepted" | "essential_only";

interface StoredConsent {
  version: string;
  choice: ConsentChoice;
  at: string;
}

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(CONSENT_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as StoredConsent;
        if (parsed.version === CONSENT_VERSION) return; // já decidiu
      }
    } catch {
      /* localStorage indisponível — mostra o banner mesmo assim */
    }
    setVisible(true);
  }, []);

  const persist = (choice: ConsentChoice) => {
    try {
      const payload: StoredConsent = {
        version: CONSENT_VERSION,
        choice,
        at: new Date().toISOString(),
      };
      localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(payload));
    } catch {
      /* ignore */
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-modal="false"
      aria-labelledby="cookie-consent-title"
      className="fixed inset-x-0 bottom-0 z-50 px-4 pb-4 sm:px-6 sm:pb-6"
    >
      <div className="mx-auto max-w-3xl rounded-xl border border-gold-400/25 bg-deep-space-900/95 p-4 shadow-2xl backdrop-blur sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <p id="cookie-consent-title" className="text-sm font-semibold text-gold-200">
              Privacidade & cookies
            </p>
            <p className="text-xs leading-relaxed text-white/70">
              Usamos apenas cookies estritamente necessários para manter sua
              sessão autenticada. Não há rastreamento de terceiros nem cookies de
              marketing dentro da plataforma. Saiba mais na{" "}
              <Link
                href="/privacy"
                className="text-gold-300 underline underline-offset-2 hover:text-gold-200"
              >
                Política de Privacidade
              </Link>
              .
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              onClick={() => persist("essential_only")}
              className="rounded-md border border-white/15 px-3 py-1.5 text-xs text-white/70 transition hover:border-white/30 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
            >
              Só essenciais
            </button>
            <button
              type="button"
              onClick={() => persist("accepted")}
              className="rounded-md border border-gold-400/50 bg-gold-400/15 px-4 py-1.5 text-xs font-medium text-gold-100 transition hover:bg-gold-400/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400/60"
            >
              Entendi
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
